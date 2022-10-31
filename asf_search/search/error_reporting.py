from typing import Dict
from asf_search import ASFSearchOptions
import requests
import logging

def report_search_error(search_options: ASFSearchOptions, message: str):
    """Reports CMR Errors automatically to ASF"""

    from asf_search import REPORT_ERRORS

    if not REPORT_ERRORS:
        logging.warning("Automatic search error reporting is turned off, search errors will NOT be reported to ASF.\
            \nTo enable automatic error reporting, set asf_search.REPORT_ERRORS to True\
            \nIf you have any questions email uso@asf.alaska.edu")
        return

    end_point_url = "https://search-error-report.asf.alaska.edu"
    
    user_agent = search_options.session.headers.get("User-Agent")
    search_options_list = '\n'.join([f"\t{option}: {key}" for option, key in dict(search_options).items()])
    message=f"Error Message: {str(message)}\nUser Agent: {user_agent} \
    \nSearch Options: {{\n{search_options_list}\n}}"

    response = requests.post(end_point_url, data={'Message': "This error message and info was automatically generated:\n\n" + message})

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"asf-search failed to automatically report an error, if you have any questions email uso@asf.alaska.edu\
            \nError Text: HTTP {response.status_code}: {response.json()['errors']}")
        return
    if response.status_code == 200:
        logging.error("The asf-search module ecountered an error with CMR, and the following message was automatically reported to ASF:\n\n" + 
                        "\"\n" +
                        message + 
                        "\n\"" +
                        "If you have any questions email uso@asf.alaska.edu")
