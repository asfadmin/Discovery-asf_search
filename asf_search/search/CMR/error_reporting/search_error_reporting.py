from typing import Dict
from asf_search import ASFSearchOptions
import requests
import logging

def report_search_error(search_options: ASFSearchOptions, message: Dict):
    """Reports CMR concept-id errorsReports"""

    end_point_url = "https://search-error-report.asf.alaska.edu"
    
    user_agent = search_options.session.headers.get("User-Agent")
    search_options_list = '\n'.join([f"\t{option}: {key}" for option, key in dict(search_options).items()])
    message=f"Error Message: {str(message)}\nUser Agent: {user_agent} \
    \nSearch Options: {{\n{search_options_list}\n}}"

    r = requests.post(end_point_url, data={'Message': "This error message and info was automatically generated:\n\n" + message})

    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.warning("asf-search failed to automatically report an error, if you have any questions email uso@asf.alaska.edu")
        return
    if r.status_code == 200:
        logging.warning("The asf-search module ecountered an error with CMR, and the following message was automatically reported to ASF:\n\n" + 
                        "\"\n" +
                        message + 
                        "\n\"" +
                        "If you have any questions email uso@asf.alaska.edu")
