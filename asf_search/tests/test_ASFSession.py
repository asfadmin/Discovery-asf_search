from importlib.resources import path
from asf_search.exceptions import ASFAuthenticationError
from ..ASFSession import ASFSession

import pytest
from unittest.mock import patch

class Test_ASFSession:
    def test_auth_with_creds_empty(self):
        session = ASFSession()
        with patch('asf_search.ASFSession.get') as mock_get:
            mock_get.return_value = "ERROR"

            with pytest.raises(ASFAuthenticationError):
                session.auth_with_creds('', '')