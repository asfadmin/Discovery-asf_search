import requests
import json
import asf_search.constants

def health() -> dict:
    return json.loads(requests.get(f'https://{asf_search.INTERNAL.HOST}{asf_search.INTERNAL.HEALTH_PATH}').text)