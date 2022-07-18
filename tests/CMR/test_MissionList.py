from asf_search.CMR.MissionList import get_campaigns
from asf_search.search.campaigns import _get_project_names
import pytest
import requests_mock

from asf_search.constants.INTERNAL import CMR_COLLECTIONS_PATH, CMR_HOST
from asf_search.exceptions import CMRError

            
def test_getMissions_error():
    with requests_mock.Mocker() as m:
        m.register_uri('POST', f"https://" + CMR_HOST + CMR_COLLECTIONS_PATH, status_code=300, json={'error': {'report': ""}})
        
        with pytest.raises(CMRError):    
            get_campaigns({})

def test_getMissions_error_parsing():
    with requests_mock.Mocker() as m:
        m.post(f"https://" + CMR_HOST + CMR_COLLECTIONS_PATH)
        
        with pytest.raises(CMRError):
            get_campaigns({})

def run_test_get_project_names(cmr_ummjson, campaigns):
    assert _get_project_names(cmr_ummjson) == campaigns
