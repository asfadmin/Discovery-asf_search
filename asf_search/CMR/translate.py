from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from asf_search.ASFSearchOptions import ASFSearchOptions
from asf_search.CMR.datasets import get_concept_id_alias
from asf_search.constants import CMR_PAGE_SIZE
import re
from shapely import wkt
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from .field_map import field_map
from .datasets import collections_per_platform
import logging

try:
    from ciso8601 import parse_datetime
except ImportError:
    from dateutil.parser import parse as parse_datetime


def translate_opts(opts: ASFSearchOptions) -> List:
    # Need to add params which ASFSearchOptions cant support (like temporal),
    # so use a dict to avoid the validate_params logic:
    dict_opts = dict(opts)

    # Escape commas for each key in the list.
    # intersectsWith, temporal, and other keys you don't want to escape, so keep whitelist instead
    for escape_commas in ['campaign']:
        if escape_commas in dict_opts:
            dict_opts[escape_commas] = dict_opts[escape_commas].replace(',', '\\,')

    dict_opts = fix_cmr_shapes(dict_opts)

    # Special case to unravel WKT field a little for compatibility
    if 'intersectsWith' in dict_opts:
        shape = wkt.loads(dict_opts.pop('intersectsWith', None))

        # If a wide rectangle is provided, make sure to use the bounding box
        # instead of the wkt for better responses from CMR
        # This will provide better results with AOI's near poles
        if should_use_bbox(shape):
            bounds = shape.boundary.bounds
            if bounds[0] > 180 or bounds[2] > 180:
                bounds = [
                    (x + 180) % 360 - 180 if idx % 2 == 0 and abs(x) > 180 else x
                    for idx, x in enumerate(bounds)
                ]

            bottom_left = [str(coord) for coord in bounds[:2]]
            top_right = [str(coord) for coord in bounds[2:]]

            bbox = ','.join([*bottom_left, *top_right])
            dict_opts['bbox'] = bbox
        else:
            (shapeType, shape) = wkt_to_cmr_shape(shape).split(':')
            dict_opts[shapeType] = shape

    # If you need to use the temporal key:
    if any(key in dict_opts for key in ['start', 'end', 'season']):
        dict_opts = fix_date(dict_opts)

    dict_opts = fix_range_params(dict_opts)

    # convert the above parameters to a list of key/value tuples
    cmr_opts = []

    # user provided umm fields
    custom_cmr_keywords = dict_opts.pop('cmr_keywords', [])

    for key, val in dict_opts.items():
        # If it's "session" or something else CMR doesn't accept, don't send it:
        if key not in field_map:
            continue
        if isinstance(val, list):
            for x in val:
                if key in ['granule_list', 'product_list']:
                    for y in x.split(','):
                        cmr_opts.append((key, y))
                else:
                    if isinstance(x, tuple):
                        cmr_opts.append((key, ','.join([str(t) for t in x])))
                    else:
                        cmr_opts.append((key, x))
        else:
            cmr_opts.append((key, val))
    # translate the above tuples to CMR key/values
    for i, opt in enumerate(cmr_opts):
        cmr_opts[i] = field_map[opt[0]]['key'], field_map[opt[0]]['fmt'].format(opt[1])

    if should_use_asf_frame(cmr_opts):
        cmr_opts = use_asf_frame(cmr_opts)

    cmr_opts.extend(custom_cmr_keywords)

    additional_keys = [
        ('page_size', CMR_PAGE_SIZE),
        ('options[temporal][and]', 'true'),
        ('sort_key[]', '-end_date'),
        ('sort_key[]', 'granule_ur'),
        ('options[platform][ignore_case]', 'true'),
        ('provider', opts.provider),
    ]

    cmr_opts.extend(additional_keys)

    return cmr_opts


def fix_cmr_shapes(fixed_params: Dict[str, Any]) -> Dict[str, Any]:
    """Fixes raw CMR lon lat coord shapes"""
    for param in ['point', 'linestring', 'circle']:
        if param in fixed_params:
            fixed_params[param] = ','.join(map(str, fixed_params[param]))

    return fixed_params


def should_use_asf_frame(cmr_opts):
    asf_frame_platforms = ['SENTINEL-1A', 'SENTINEL-1B', 'ALOS']

    asf_frame_collections = get_concept_id_alias(asf_frame_platforms, collections_per_platform)

    return any(
        [
            p[0] == 'platform[]'
            and p[1].upper() in asf_frame_platforms
            or p[0] == 'echo_collection_id[]'
            and p[1] in asf_frame_collections
            for p in cmr_opts
        ]
    )


def use_asf_frame(cmr_opts):
    """
    Sentinel/ALOS: always use asf frame instead of esa frame

    Platform-specific hack
    We do them at the subquery level in case the main query crosses
    platforms that don't suffer these issue.
    """

    for n, p in enumerate(cmr_opts):
        if not isinstance(p[1], str):
            continue

        m = re.search(r'CENTER_ESA_FRAME', p[1])
        if m is None:
            continue

        logging.debug('Sentinel/ALOS subquery, using ASF frame instead of ESA frame')

        cmr_opts[n] = (p[0], p[1].replace(',CENTER_ESA_FRAME,', ',FRAME_NUMBER,'))

    return cmr_opts


# some products don't have integer values in BYTES fields, round to nearest int
def try_round_float(value: str) -> Optional[int]:
    if value is None:
        return None

    value = float(value)
    return round(value)


def try_parse_int(value: str) -> Optional[int]:
    if value is None:
        return None

    return int(value)


def try_parse_float(value: str) -> Optional[float]:
    if value is None:
        return None

    return float(value)


def try_parse_date(value: str) -> Optional[str]:
    if value is None:
        return None

    try:
        date = parse_datetime(value)
    except ValueError:
        return None

    if date is None:
        return value

    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
        # Turn all inputs into a consistant format:

    return date.strftime('%Y-%m-%dT%H:%M:%SZ')


def fix_date(fixed_params: Dict[str, Any]):
    if 'start' in fixed_params or 'end' in fixed_params or 'season' in fixed_params:
        fixed_params['start'] = (
            fixed_params['start'] if 'start' in fixed_params else '1978-01-01T00:00:00Z'
        )
        fixed_params['end'] = (
            fixed_params['end'] if 'end' in fixed_params else datetime.now(timezone.utc).isoformat()
        )
        fixed_params['season'] = (
            ','.join(str(x) for x in fixed_params['season']) if 'season' in fixed_params else ''
        )

        fixed_params['temporal'] = (
            f'{fixed_params["start"]},{fixed_params["end"]},{fixed_params["season"]}'
        )

        # And a little cleanup
        fixed_params.pop('start', None)
        fixed_params.pop('end', None)
        fixed_params.pop('season', None)

    return fixed_params


def fix_range_params(fixed_params: Dict[str, Any]) -> Dict[str, Any]:
    """Converts ranges to comma separated strings"""
    for param in [
        'offNadirAngle',
        'relativeOrbit',
        'absoluteOrbit',
        'frame',
        'asfFrame',
    ]:
        if param in fixed_params.keys() and isinstance(fixed_params[param], list):
            fixed_params[param] = ','.join([str(val) for val in fixed_params[param]])

    return fixed_params


def should_use_bbox(shape: BaseGeometry):
    """
    If the passed shape is a polygon, and if that polygon
    is equivalent to it's bounding box (if it's a rectangle),
    we should use the bounding box to search instead
    """
    if isinstance(shape, Polygon):
        coords = [
            [shape.bounds[0], shape.bounds[1]],
            [shape.bounds[2], shape.bounds[1]],
            [shape.bounds[2], shape.bounds[3]],
            [shape.bounds[0], shape.bounds[3]],
        ]
        return shape.equals(Polygon(shell=coords))

    return False


def wkt_to_cmr_shape(shape: BaseGeometry):
    # take note of the WKT type
    if shape.geom_type not in ['Point', 'LineString', 'Polygon']:
        raise ValueError('Unsupported WKT: {0}.'.format(shape.wkt))

    if shape.geom_type == 'Polygon':
        coords = shape.exterior.coords
    else:  # type == Point | Linestring
        coords = shape.coords
    # Turn [[x,y],[x,y]] into [x,y,x,y]:
    lon_lat_sequence = []
    for lon_lat in coords:
        lon_lat_sequence.extend(lon_lat)
    # Turn any "6e8" to a literal number. (As a sting):
    coords = ['{:.16f}'.format(float(cord)) for cord in lon_lat_sequence]
    return '{0}:{1}'.format(shape.geom_type.lower(), ','.join(coords))
