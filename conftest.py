import argparse
import pytest
import os
from asf_search.ASFSession import ASFSession
from getpass import getpass

def string_to_session(user_input: str) -> ASFSession:
    session = ASFSession()

    if user_input is not None and len(user_input):
        session.auth_with_token(user_input)

    return session

def set_should_auth_session(user_input: str) -> ASFSession:
    should_auth = string_to_bool(user_input)
    session = ASFSession()
    if should_auth:
        if (token:=os.environ.get('EDL_TOKEN')) is not None:
            try:
                session.auth_with_token(token=token)
            except Exception as exc:
                raise argparse.ArgumentTypeError(f"Unabled to authenticate with the given environment's `EDL_TOKEN` (token may need to be refreshed). Original exception: {str(exc)}")
        else:
            raise argparse.ArgumentTypeError("ERROR: Environment variable `EDL_TOKEN` token not set, cannot create authenticated session for tests. Are you running this in the correct local/github action environment?")

    return session

def set_should_auth_session_with_creds(user_input: str) -> ASFSession:
    should_auth = string_to_bool(user_input)
    session = ASFSession()
    if should_auth:
        session.auth_with_creds(input('EDL Username'), getpass('EDL Password'))

    return session

def set_should_auth_session_with_token(user_input: str) -> ASFSession:
    should_auth = string_to_bool(user_input)
    session = ASFSession()
    if should_auth:
        session.auth_with_token(getpass('EDL Token'))

    return session

def string_to_bool(user_input: str) -> bool:
    user_input = str(user_input).upper()
    if 'TRUE'.startswith(user_input):
       return True
    elif 'FALSE'.startswith(user_input):
       return False
    else:
       raise argparse.ArgumentTypeError(f"ERROR: Could not convert '{user_input}' to bool (true/false/t/f).")

def pytest_addoption(parser: pytest.Parser):
    parser.addoption("--should_auth_session", action="store", dest="authenticated_session", type=set_should_auth_session, default='FALSE',
        help = "'should_auth_session': Set if the test case requires authentication (pull from `EDL_TOKEN` environment variable)"
    )

    parser.addoption("--auth_with_creds", action="store", dest="authenticated_session", type=set_should_auth_session_with_creds, default='FALSE',
                     help = "'auth_with_creds': Use EDL username and password to authenticate session for relevant tests")

    parser.addoption("--auth_with_token", action="store", dest="authenticated_session", type=set_should_auth_session_with_token, default='FALSE',
                     help = "'auth_with_creds': Use EDL token to authenticate session for relevant tests")
