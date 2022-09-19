import re
from typing import Dict
from asf_search import ASFSearchOptions
import requests

def push_concept_id_error(search_options: ASFSearchOptions, message: Dict):
    """Reports CMR concept-id errorsReports"""

    end_point_url = "asf-search-concept-id-error.asf.alaska.edu"
    
    user_agent = search_options.session.headers.get("User-Agent")
    client_id = search_options.session.headers.get("Client-Id")
    search_options_list = '\n'.join([f"\t{option}: {key}" for option, key in dict(search_options).items()])
    message=f"User Agent: {user_agent}\nClient ID: {client_id}\nError Message: {str(message)} \
    \nSearch Options: {{\n{search_options_list}\n}}"

    r = requests.post(end_point_url, data={'Message': message})
