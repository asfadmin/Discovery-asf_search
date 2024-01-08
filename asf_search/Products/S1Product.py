import copy
from typing import Union
from asf_search import ASFSearchOptions, ASFSession, ASFProduct
from asf_search.CMR.translate import try_parse_int
from asf_search.constants import PLATFORM
from asf_search.constants import PRODUCT_TYPE

class S1Product(ASFProduct):
    """
    The S1Product classes covers most Sentinel-1 Products
    (For S1 BURST-SLC, OPERA-S1, and ARIA-S1 GUNW Products, see relevant S1 subclasses)

    ASF Dataset Overview Page: https://asf.alaska.edu/datasets/daac/sentinel-1/
    """

    _base_properties = {
        'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0], 'cast': try_parse_int}, #Sentinel and ALOS product alt for frameNumber (ESA_FRAME)
        'groupID': {'path': [ 'AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
        'md5sum': {'path': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'pgeVersion': {'path': ['PGEVersionClass', 'PGEVersion']},
    }
    """
    S1 Specific path override
    - frameNumber: overrides ASFProduct's `CENTER_ESA_FRAME` with `FRAME_NUMBER`
    """

    baseline_type = ASFProduct.BaselineCalcType.CALCULATED
    
    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        baseline = self.get_baseline_calc_properties()
        
        if baseline is not None:
            if None not in baseline['stateVectors']['positions'].values() and len(baseline['stateVectors'].items()) > 0:
                self.baseline = baseline
        


    def get_baseline_calc_properties(self) -> dict:
        """
        :returns properties required for SLC baseline stack calculations
        """
        ascendingNodeTime = self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'ASC_NODE_TIME'), 'Values', 0)

        if ascendingNodeTime is not None:
            if not ascendingNodeTime.endswith('Z'):
                ascendingNodeTime += 'Z'
        
        return {
            'stateVectors': self.get_state_vectors(),
            'ascendingNodeTime': ascendingNodeTime
        }
    
    def get_state_vectors(self) -> dict:
        """
        Used in spatio-temporal perpendicular baseline calculations for non-pre-calculated stacks

        :returns dictionary of pre/post positions, velocities, and times"""
        positions = {}
        velocities = {}

        positions['prePosition'], positions['prePositionTime'] = self.umm_cast(self._get_state_vector, self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'SV_POSITION_PRE'), 'Values', 0))
        positions['postPosition'], positions['postPositionTime'] = self.umm_cast(self._get_state_vector, self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'SV_POSITION_POST'), 'Values', 0))
        velocities['preVelocity'], velocities['preVelocityTime'] = self.umm_cast(self._get_state_vector, self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'SV_VELOCITY_PRE'), 'Values', 0))
        velocities['postVelocity'], velocities['postVelocityTime'] = self.umm_cast(self._get_state_vector, self.umm_get(self.umm, 'AdditionalAttributes', ('Name', 'SV_VELOCITY_POST'), 'Values', 0))

        for key in ['prePositionTime','postPositionTime','preVelocityTime','postVelocityTime']:
            if positions.get(key) is not None:
                if not positions.get(key).endswith('Z'):
                    positions[key] += 'Z'

        return {
            'positions': positions,
            'velocities': velocities
        }
    
    @staticmethod
    def _get_state_vector(state_vector: str):
        if state_vector is None:
            return None, None
        
        return list(map(float, state_vector.split(',')[:3])), state_vector.split(',')[-1]

    def get_stack_opts(self, opts: ASFSearchOptions = None) -> ASFSearchOptions:
        """
        Returns the search options asf-search will use internally to build an SLC baseline stack from
        
        :param opts: additional criteria for limiting 
        :returns ASFSearchOptions used for build Sentinel-1 SLC Stack
        """
        stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        
        stack_opts.processingLevel = self.get_default_baseline_product_type()
        stack_opts.beamMode = [self.properties['beamModeType']]
        stack_opts.flightDirection = self.properties['flightDirection']
        stack_opts.relativeOrbit = [int(self.properties['pathNumber'])] # path
        stack_opts.platform = [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B]
        stack_opts.polarization = ['HH','HH+HV'] if self.properties['polarization'] in ['HH','HH+HV'] else ['VV', 'VV+VH']
        stack_opts.intersectsWith = self.centroid().wkt
        
        return stack_opts
    
    @staticmethod
    def get_property_paths() -> dict:
        return {
            **ASFProduct.get_property_paths(),
            **S1Product._base_properties
        }

    def is_valid_reference(self) -> bool:
        """perpendicular baselines are not pre-calculated for S1 products and require position/velocity state vectors to calculate"""
        return self.valid_state_vectors()
    
    def valid_state_vectors(self) -> bool:
        for key in ['postPosition', 'postPositionTime', 'prePosition', 'postPositionTime']:
            if key not in self.baseline['stateVectors']['positions'] or self.baseline['stateVectors']['positions'][key] == None:
                return False
        return True
    
    @staticmethod
    def get_default_baseline_product_type() -> Union[str, None]:
        """
        Returns the product type to search for when building a baseline stack.
        """
        return PRODUCT_TYPE.SLC