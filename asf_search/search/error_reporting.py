from asf_search import ASF_LOGGER, ASFSearchOptions
from asf_search import INTERNAL
import requests



def report_search_error(search_options: ASFSearchOptions, message: str):
    """Reports CMR Errors automatically to ASF"""

    from asf_search import REPORT_ERRORS

    if not REPORT_ERRORS:
        ASF_LOGGER.warning(
            'Automatic search error reporting is turned off,'
            'search errors will NOT be reported to ASF.'
            '\nTo enable automatic error reporting, set asf_search.REPORT_ERRORS to True'
            '\nIf you have any questions email uso@asf.alaska.edu'
        )
        return

    user_agent = search_options.session.headers.get('User-Agent')
    search_options_list = '\n'.join(
        [f'\t{option}: {key}' for option, key in dict(search_options).items()]
    )
    message = f'Error Message: {str(message)}\nUser Agent: {user_agent} \
    \nSearch Options: {{\n{search_options_list}\n}}'

    response = requests.post(
        f'https://{INTERNAL.ERROR_REPORTING_ENDPOINT}',
        data={'Message': f'This error message and info was automatically generated:\n\n{message}'},
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        ASF_LOGGER.error(
            'asf-search failed to automatically report an error,'
            'if you have any questions email uso@asf.alaska.edu'
            f"\nError Text: HTTP {response.status_code}: {response.json()['errors']}"
        )
        return
    if response.status_code == 200:
        ASF_LOGGER.error(
            (
                'The asf-search module ecountered an error with CMR,'
                'and the following message was automatically reported to ASF:'
                '\n\n"\nmessage\n"'
                'If you have any questions email uso@asf.alaska.edu'
            )
        )
