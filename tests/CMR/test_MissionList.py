from asf_search.CMR.MissionList import getMissions

import pytest
import requests_mock

from asf_search.constants.INTERNAL import CMR_COLLECTIONS, CMR_HOST
from asf_search.exceptions import CMRError

            
def test_getMissions_error():
    with requests_mock.Mocker() as m:
        m.register_uri('POST', f"https://" + CMR_HOST + CMR_COLLECTIONS, status_code=300, json={'error': {'report': ""}})
        
        with pytest.raises(CMRError):    
            getMissions({})

def test_getMissions_error_parsing():
    with requests_mock.Mocker() as m:
        m.post(f"https://" + CMR_HOST + CMR_COLLECTIONS)
        
        with pytest.raises(CMRError):
            getMissions({})
