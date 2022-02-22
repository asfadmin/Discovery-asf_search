from asf_search.ASFCollection import ASFCollection
from asf_search.CMR import MissionList

def collection_search(platform: str):
    data = {
                'include_facets': 'true',
                'provider': 'ASF'
            }

    if platform != None:
        if platform == 'UAVSAR':
            data['platform[]'] = 'G-III'
            data['instrument[]'] = 'UAVSAR'
        elif platform == 'AIRSAR':
            data['platform[]'] = 'DC-8'
            data['instrument[]'] = 'AIRSAR'
        elif platform == 'SENTINEL-1 INTERFEROGRAM (BETA)':
            data['platform[]'] = 'SENTINEL-1A'
        else:
            data['platform[]'] = platform
    return [
        *map(lambda mission: ASFCollection(platform, mission), 
            MissionList.getMissions(data))
        ]
