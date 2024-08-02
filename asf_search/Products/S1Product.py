import copy
from typing import Dict, List, Optional, Tuple
from asf_search import ASFSearchOptions, ASFSession, ASFStackableProduct
from asf_search.CMR.translate import try_parse_date
from asf_search.CMR.translate import try_parse_int
from asf_search.constants import PLATFORM
from asf_search.constants import PRODUCT_TYPE


class S1Product(ASFStackableProduct):
    """
    The S1Product classes covers most Sentinel-1 Products
    (For S1 BURST-SLC, OPERA-S1, and ARIA-S1 GUNW Products, see relevant S1 subclasses)

    ASF Dataset Overview Page: https://asf.alaska.edu/datasets/daac/sentinel-1/
    """

    _base_properties = {
        **ASFStackableProduct._base_properties,
        'frameNumber': {
            'path': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0],
            'cast': try_parse_int,
        },  # Sentinel and ALOS product alt for frameNumber (ESA_FRAME)
        'groupID': {'path': ['AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
        'md5sum': {'path': ['AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'pgeVersion': {'path': ['PGEVersionClass', 'PGEVersion']},
    }
    """
    S1 Specific path override
    - frameNumber: overrides ASFProduct's `CENTER_ESA_FRAME` with `FRAME_NUMBER`
    """

    baseline_type = ASFStackableProduct.BaselineCalcType.CALCULATED

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        self.properties['s3Urls'] = self._get_s3_urls()

        if self.has_baseline():
            self.baseline = self.get_baseline_calc_properties()

    def has_baseline(self) -> bool:
        baseline = self.get_baseline_calc_properties()

        return baseline is not None and None not in baseline['stateVectors']['positions'].values()

    def get_baseline_calc_properties(self) -> Dict:
        """
        :returns properties required for SLC baseline stack calculations
        """
        ascendingNodeTime = self.umm_cast(
            self._parse_timestamp,
            self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'ASC_NODE_TIME'), 'Values', 0),
        )

        return {
            'stateVectors': self.get_state_vectors(),
            'ascendingNodeTime': ascendingNodeTime,
        }

    def get_state_vectors(self) -> Dict:
        """
        Used in spatio-temporal perpendicular baseline calculations for non-pre-calculated stacks

        :returns dictionary of pre/post positions, velocities, and times"""
        positions = {}
        velocities = {}

        sv_pre_position = self.umm_get(
            self.umm, 'AdditionalAttributes', ('Name', 'SV_POSITION_PRE'), 'Values', 0
        )
        sv_post_position = self.umm_get(
            self.umm, 'AdditionalAttributes', ('Name', 'SV_POSITION_POST'), 'Values', 0
        )
        sv_pre_velocity = self.umm_get(
            self.umm, 'AdditionalAttributes', ('Name', 'SV_VELOCITY_PRE'), 'Values', 0
        )
        sv_post_velocity = self.umm_get(
            self.umm, 'AdditionalAttributes', ('Name', 'SV_VELOCITY_POST'), 'Values', 0
        )

        positions['prePosition'], positions['prePositionTime'] = self.umm_cast(
            self._parse_state_vector, sv_pre_position
        )
        positions['postPosition'], positions['postPositionTime'] = self.umm_cast(
            self._parse_state_vector, sv_post_position
        )
        velocities['preVelocity'], velocities['preVelocityTime'] = self.umm_cast(
            self._parse_state_vector, sv_pre_velocity
        )
        velocities['postVelocity'], velocities['postVelocityTime'] = self.umm_cast(
            self._parse_state_vector, sv_post_velocity
        )

        return {'positions': positions, 'velocities': velocities}

    def _parse_timestamp(self, timestamp: str) -> Optional[str]:
        if timestamp is None:
            return None

        return try_parse_date(timestamp)

    def _parse_state_vector(self, state_vector: str) -> Tuple[Optional[List], Optional[str]]:
        if state_vector is None:
            return None, None

        velocity = [float(val) for val in state_vector.split(',')[:3]]
        timestamp = self._parse_timestamp(state_vector.split(',')[-1])

        return velocity, timestamp

    def get_stack_opts(self, opts: ASFSearchOptions = None) -> ASFSearchOptions:
        """
        Returns the search options asf-search will use internally
        to build an SLC baseline stack from

        :param opts: additional criteria for limiting
        :returns ASFSearchOptions used for build Sentinel-1 SLC Stack
        """
        stack_opts = ASFSearchOptions() if opts is None else copy(opts)

        stack_opts.processingLevel = self.get_default_baseline_product_type()
        stack_opts.beamMode = [self.properties['beamModeType']]
        stack_opts.flightDirection = self.properties['flightDirection']
        stack_opts.relativeOrbit = [int(self.properties['pathNumber'])]  # path
        stack_opts.platform = [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B]

        if self.properties['polarization'] in ['HH', 'HH+HV']:
            stack_opts.polarization = ['HH', 'HH+HV']
        else:
            stack_opts.polarization = ['VV', 'VV+VH']

        stack_opts.intersectsWith = self.centroid().wkt

        return stack_opts

    def is_valid_reference(self) -> bool:
        keys = ['postPosition', 'postPositionTime', 'prePosition', 'postPositionTime']

        for key in keys:
            if self.baseline['stateVectors']['positions'].get(key) is None:
                return False

        return True

    @staticmethod
    def get_default_baseline_product_type() -> str:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return PRODUCT_TYPE.SLC
