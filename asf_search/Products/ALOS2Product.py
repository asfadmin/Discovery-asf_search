from copy import copy
from typing import Dict, Union

from asf_search import ASFSearchOptions, ASFSession, ASFStackableProduct
from asf_search.CMR.translate import try_parse_float, try_parse_int, try_round_float
from asf_search.constants import PRODUCT_TYPE

class ALOS2Product(ASFStackableProduct):
    """
    Used for ALOS Palsar and Avnir dataset products

    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/alos-palsar/
    """

    _base_properties = {
        **ASFStackableProduct._base_properties,
        'frameNumber': {
            'path': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0],
            'cast': try_parse_int,
        },  # Sentinel and ALOS product alt for frameNumber (ESA_FRAME)
        'center_lat': {
            'path': ['AdditionalAttributes', ('Name', 'CENTER_LAT'), 'Values', 0],
            'cast': try_parse_float,
        },
        'center_lon': {
            'path': ['AdditionalAttributes', ('Name', 'CENTER_LON'), 'Values', 0],
            'cast': try_parse_float,
        },'faradayRotation': {
            'path': ['AdditionalAttributes', ('Name', 'FARADAY_ROTATION'), 'Values', 0],
            'cast': try_parse_float,
        },
        'offNadirAngle': {
            'path': ['AdditionalAttributes', ('Name', 'OFF_NADIR_ANGLE'), 'Values', 0],
            'cast': try_parse_float,
        },
        'bytes': {
            'path': ['DataGranule', 'ArchiveAndDistributionInformation', 0, 'SizeInBytes'],
            'cast': try_round_float,
        },
        'beamModeType': {'path': ['AdditionalAttributes', ('Name', 'BEAM_MODE_TYPE'), 'Values', 0]},
        'polarization': {
            'path': ['AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values']
        },  # dual polarization is in list rather than a 'VV+VH' style format
    }

    baseline_type = ASFStackableProduct.BaselineCalcType.CALCULATED


    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)
        self.properties.pop('md5sum')
        self.properties.pop('granuleType')
        self.properties.pop('processingLevel')
        
        self.baseline = self.get_baseline_calc_properties()

    def get_baseline_calc_properties(self) -> Dict:
        """
        :returns properties required for SLC baseline stack calculations
        """
        return {'stateVectors': self.get_state_vectors()}

    def get_stack_opts(self, opts: ASFSearchOptions = None) -> ASFSearchOptions:
        """
        Returns the search options asf-search will use internally
        to build an SLC baseline stack from

        :param opts: additional criteria for limiting
        :returns ASFSearchOptions used for build Sentinel-1 SLC Stack
        """
        stack_opts = ASFSearchOptions() if opts is None else copy(opts)

        stack_opts.beamMode = [self.properties['beamModeType']]
        stack_opts.flightDirection = self.properties['flightDirection']
        stack_opts.relativeOrbit = [int(self.properties['pathNumber'])]  # path
        stack_opts.dataset = 'ALOS-2'
        
        if any(e in ['HH', 'HH+HV'] for e in self.properties['polarization']):
            stack_opts.polarization = ['HH', 'HH+HV']
        else:
            stack_opts.polarization = ['VV', 'VV+VH']

        stack_opts.intersectsWith = self.centroid().wkt

        return stack_opts

    def get_state_vectors(self) -> Dict:
        """
        Used in spatio-temporal perpendicular baseline calculations for non-pre-calculated stacks

        :returns dictionary of pre/post positions, velocities, and times"""

        position = [
            float(val)
            for val in self.umm_get(
                self.umm, 'AdditionalAttributes', ('Name', 'SV_POSITION'), 'Values'
            )
        ]
        velocity = [
            float(val)
            for val in self.umm_get(
                self.umm, 'AdditionalAttributes', ('Name', 'SV_VELOCITY'), 'Values'
            )
        ]

        return dict(position=position, velocity=velocity)

    def is_valid_reference(self):
        return self.has_baseline()
