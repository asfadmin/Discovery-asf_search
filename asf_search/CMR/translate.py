from asf_search.ASFSearchOptions import ASFSearchOptions

from .field_map import field_map


def translate_opts(opts: ASFSearchOptions) -> list:
    # Start by just grabbing the searchable parameters
    dict_opts = dict(opts)

    # convert the above parameters to a list of key/value tuples
    cmr_opts = []
    for (key, val) in dict_opts.items():
        if isinstance(val, list):
            for x in val:
                cmr_opts.append((key, x))
        else:
            cmr_opts.append((key, val))

    # translate the above tuples to CMR key/values
    for i, opt in enumerate(cmr_opts):
        cmr_opts[i] = field_map[opt[0]]['key'], field_map[opt[0]]['fmt'].format(opt[1])

    return cmr_opts


def translate_product(item: dict) -> dict:
    new = dict({
        'geometry': {'coordinates': []},
        'properties': {},
        'type': 'Feature'
    })

    coords = item['umm']['SpatialExtent']['HorizontalSpatialDomain']['Geometry']['GPolygons'][0]['Boundary']['Points']
    coords = [[c['Longitude'], c['Latitude']] for c in coords]
    new['geometry']['coordinates'] = [coords]

    return new
