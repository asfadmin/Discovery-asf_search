import requests
import json
import asf_search.constants

def health() -> dict:
    """
    Checks basic connectivity to and health of the public ASF Search API.

    :return: Current configuration and status of subsystems
    """
    return json.loads(requests.get(f'https://{asf_search.INTERNAL.HOST}{asf_search.INTERNAL.HEALTH_PATH}').text)