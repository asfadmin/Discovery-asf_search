from typing import Dict, List, Union
from asf_search.CMR.MissionList import get_collections


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
    
    missions = get_collections(data)
    mission_names = _get_project_names(missions)

    return mission_names


def _get_project_names(data: Union[Dict, List]) -> List[str]:
    output = []
    if isinstance(data, Dict):
        for key, value in data.items():
            if key == "Projects":
                return [list(item.values())[0] for item in value]
            output.extend(_get_project_names(value))
    elif isinstance(data, List):
        for item in data:
            output.extend(_get_project_names(item))
    
    return output
