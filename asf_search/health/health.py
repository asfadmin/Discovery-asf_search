import requests
import json

import asf_search.constants

def health(host: str = None) -> dict:
    """
    Checks basic connectivity to and health of the ASF SearchAPI.

    :param host: SearchAPI host, defaults to Production SearchAPI. This option is intended for dev/test purposes.
    :return: Current configuration and status of subsystems
    """

    if host is None:
        host = asf_search.INTERNAL.CMR_HOST
    return json.loads(requests.get(f'https://{host}{asf_search.INTERNAL.CMR_HEALTH_PATH}').text)