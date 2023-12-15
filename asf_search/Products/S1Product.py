import copy
from asf_search import ASFSearchOptions, ASFSession, ASFProduct
from asf_search.CMR.translate import get_state_vector, get as umm_get, cast as umm_cast, try_parse_int
from asf_search.baseline import BaselineCalcType
from asf_search.constants import PLATFORM

class S1Product(ASFProduct):
    base_properties = {
        'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0], 'cast': try_parse_int}, #Sentinel and ALOS product alt for frameNumber (ESA_FRAME)
        'polarization': {'path': [ 'AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values', 0]},
        'granuleType': {'path': [ 'AdditionalAttributes', ('Name', 'GRANULE_TYPE'), 'Values', 0], },
        'groupID': {'path': [ 'AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0], },
        'md5sum': {'path': [ 'AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0], },
        'orbit': {'path': [ 'OrbitCalculatedSpatialDomains', 0, 'OrbitNumber'], 'cast': try_parse_int},
        'pgeVersion': {'path': ['PGEVersionClass', 'PGEVersion'], },
        'processingDate': {'path': [ 'DataGranule', 'ProductionDateTime'], },
        'sensor': {'path': [ 'Platforms', 0, 'Instruments', 0, 'ShortName'], },
    }

    baseline_type = BaselineCalcType.CALCULATED
    
    def __init__(self, args: dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        baseline = self.get_baseline_calc_properties()
        
        if baseline is not None:
            if None not in baseline['stateVectors']['positions'].values() and len(baseline['stateVectors'].items()) > 0:
                self.baseline = baseline
        


    def get_baseline_calc_properties(self) -> dict:
        ascendingNodeTime = umm_get(self.umm, 'AdditionalAttributes', ('Name', 'ASC_NODE_TIME'), 'Values', 0)

        if ascendingNodeTime is not None:
            if not ascendingNodeTime.endswith('Z'):
                ascendingNodeTime += 'Z'
        
        return {
            'stateVectors': self.get_state_vectors(),
            'ascendingNodeTime': ascendingNodeTime
        }
    
    def get_state_vectors(self) -> dict:
        positions = {}
        velocities = {}

        positions['prePosition'], positions['prePositionTime'] = umm_cast(get_state_vector, umm_get(self.umm, 'AdditionalAttributes', ('Name', 'SV_POSITION_PRE'), 'Values', 0))
        positions['postPosition'], positions['postPositionTime'] = umm_cast(get_state_vector, umm_get(self.umm, 'AdditionalAttributes', ('Name', 'SV_POSITION_POST'), 'Values', 0))
        velocities['preVelocity'], velocities['preVelocityTime'] = umm_cast(get_state_vector, umm_get(self.umm, 'AdditionalAttributes', ('Name', 'SV_VELOCITY_PRE'), 'Values', 0))
        velocities['postVelocity'], velocities['postVelocityTime'] = umm_cast(get_state_vector, umm_get(self.umm, 'AdditionalAttributes', ('Name', 'SV_VELOCITY_POST'), 'Values', 0))

        for key in ['prePositionTime','postPositionTime','preVelocityTime','postVelocityTime']:
            if positions.get(key) is not None:
                if not positions.get(key).endswith('Z'):
                    positions[key] += 'Z'

        return {
            'positions': positions,
            'velocities': velocities
        }
    
    def get_stack_opts(self, 
                       opts: ASFSearchOptions = None):

        stack_opts = (ASFSearchOptions() if opts is None else copy(opts))
        
        stack_opts.processingLevel = S1Product.get_default_product_type()
        stack_opts.beamMode = [self.properties['beamModeType']]
        stack_opts.flightDirection = self.properties['flightDirection']
        stack_opts.relativeOrbit = [int(self.properties['pathNumber'])] # path
        stack_opts.platform = [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B]
        stack_opts.polarization = ['HH','HH+HV'] if self.properties['polarization'] in ['HH','HH+HV'] else ['VV', 'VV+VH']
        stack_opts.intersectsWith = self.centroid().wkt
        
        return stack_opts
        # return {
        #     'processingLevel': 'SLC',
        #     'beamMode': [self.properties['beamModeType']],
        #     'flightDirection': self.properties['flightDirection'],
        #     'relativeOrbit': [int(self.properties['pathNumber'])], # path
        #     'platform': [PLATFORM.SENTINEL1A, PLATFORM.SENTINEL1B],
        #     'polarization': ['HH','HH+HV'] if self.properties['polarization'] in ['HH','HH+HV'] else ['VV', 'VV+VH'],
        #     'intersectsWith': self.centroid().wkt
        # }
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
            **S1Product.base_properties
        }
    
    @staticmethod
    def get_default_product_type():
        return 'SLC'

    def is_valid_reference(self):
        return self.valid_state_vectors()
    
    def valid_state_vectors(self):
        for key in ['postPosition', 'postPositionTime', 'prePosition', 'postPositionTime']:
            if key not in self.baseline['stateVectors']['positions'] or self.baseline['stateVectors']['positions'][key] == None:
                return False
        return True