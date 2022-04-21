from typing import Dict, List, Union
from asf_search.CMR.MissionList import get_campaigns


def campaigns(platform: str) -> List[str]:
    """
    Returns a list of campaign names for the given platform, 
    each name being usable as a campaign for asf_search.search() and asf_search.geo_search()

    :param platform: The name of the platform to gather campaign names for. 
    Platforms currently supported include UAVSAR, AIRSAR, and SENTINEL-1 INTERFEROGRAM (BETA)
    
    :return: A list of campaign names for the given platform
    """
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
    
    missions = get_campaigns(data)
    mission_names = _get_project_names(missions)

    return mission_names


def _get_project_names(data: Union[Dict, List]) -> List[str]:
    """
    Recursively searches for campaign names 
    under "Projects" key in CMR umm_json response

    :param data: CMR umm_json response

    :return: A list of found campaign names for the given platform
    """
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
