import copy
from asf_search import ASFSession, ASFProduct
from asf_search.CMR.translate import get_state_vector, get as umm_get, cast as umm_cast
from asf_search.CMR.UMMFields import umm_property_paths
from asf_search.constants import PLATFORM

class S1Product(ASFProduct):
    base_properties = {
        'frameNumber',
        'polarization',
        'bytes',
        'granuleType',
        'groupID',
        'md5sum',
        'orbit',
        'pgeVersion',
        'processingDate',
        'sensor'
    }

    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        baseline = self.get_baseline_calc_properties()
        if None not in baseline['stateVectors']['positions'].values() and len(baseline['stateVectors'].items()) > 0:
            self.baseline = baseline
        
        self.properties['frameNumber'] = umm_cast(int, umm_get(self.umm, *umm_property_paths.get('S1AlosFrameNumber')))


    def get_baseline_calc_properties(self) -> dict:
        ascendingNodeTime = umm_get(self.umm, *umm_property_paths['ascendingNodeTime'])

        return {
            'stateVectors': self.get_state_vectors(),
            'ascendingNodeTime': ascendingNodeTime
        }
    
    def get_state_vectors(self) -> dict:
        positions = {}
        velocities = {}
        positions['prePosition'], positions['prePositionTime'] = umm_cast(get_state_vector, umm_get(self.umm, *umm_property_paths['sv_position_pre']))
        positions['postPosition'], positions['postPositionTime'] = umm_cast(get_state_vector, umm_get(self.umm, *umm_property_paths['sv_position_post']))
        velocities['preVelocity'], velocities['preVelocityTime'] = umm_cast(get_state_vector, umm_get(self.umm, *umm_property_paths['sv_velocity_pre']))
        velocities['postVelocity'], velocities['postVelocityTime'] = umm_cast(get_state_vector, umm_get(self.umm, *umm_property_paths['sv_velocity_post']))

        return {
            'positions': positions,
            'velocities': velocities
        }
    
    def get_stack_opts(self):

        # stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        return {
            'processingLevel': 'SLC',
            'beamMode': [self.properties['beamModeType']],
            'flightDirection': self.properties['flightDirection'],
            'relativeOrbit': [int(self.properties['pathNumber'])], # path
            'platform': [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B],
            'polarization': ['HH','HH+HV'] if self.properties['polarization'] in ['HH','HH+HV'] else ['VV', 'VV+VH'],
            'intersectsWith': self.centroid().wkt
        }
        # if reference.properties['processingLevel'] == 'BURST':
        #     stack_opts.processingLevel = 'BURST'
        # else:
        #     stack_opts.processingLevel = 'SLC'
        
        # if reference.properties['processingLevel'] == 'BURST':
        #     stack_opts.fullBurstID = reference.properties['burst']['fullBurstID']
        #     stack_opts.polarization = [reference.properties['polarization']]
        #     return stack_opts
        
        # stack_opts.platform = [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B]
        
        # stack_opts.beamMode = [reference.properties['beamModeType']]
        # stack_opts.flightDirection = reference.properties['flightDirection']
        # stack_opts.relativeOrbit = [int(reference.properties['pathNumber'])]  # path
        
        # if reference.properties['polarization'] in ['HH', 'HH+HV']:
        #     stack_opts.polarization = ['HH','HH+HV']
        # elif reference.properties['polarization'] in ['VV', 'VV+VH']:
        #     stack_opts.polarization = ['VV','VV+VH']
        # else:
        #     stack_opts.polarization = [reference.properties['polarization']]
        
        # stack_opts.intersectsWith = reference.centroid().wkt
        # return stack_opts

    @staticmethod
    def _get_property_paths() -> dict:
        return {
            **ASFProduct._get_property_paths(),
            **{
                prop: umm_path 
                for prop in S1Product.base_properties 
                if (umm_path := umm_property_paths.get(prop)) is not None
            },
        }
    
    def get_default_product_type(self):
        return 'SLC'
    
    @staticmethod
    def is_valid_product(item: dict):
        platform: str = ASFProduct.get_platform(item).lower()

        return platform in ['sentinel-1', 'sentinel-1a', 'sentinel-1b']