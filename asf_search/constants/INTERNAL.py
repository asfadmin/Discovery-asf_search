ASF_AUTH_HOST = 'auth.asf.alaska.edu'

CMR_HOST = 'cmr.earthdata.nasa.gov'
CMR_HOST_UAT = 'cmr.uat.earthdata.nasa.gov'
CMR_TIMEOUT = 30
CMR_FORMAT_EXT = 'umm_json'
CMR_GRANULE_PATH = f'/search/granules.{CMR_FORMAT_EXT}'
CMR_COLLECTIONS = '/search/collections'
CMR_COLLECTIONS_PATH = f'{CMR_COLLECTIONS}.{CMR_FORMAT_EXT}'
CMR_HEALTH_PATH = '/search/health'
CMR_PAGE_SIZE = 250
EDL_HOST = 'urs.earthdata.nasa.gov'
EDL_HOST_UAT = f'uat.{EDL_HOST}'

EDL_CLIENT_ID = 'BO_n7nTIlMljdvU6kRRB3g'

DEFAULT_PROVIDER = 'ASF'

AUTH_DOMAINS = ['asf.alaska.edu', 'earthdata.nasa.gov'] #, 'earthdatacloud.nasa.gov']
AUTH_COOKIES = ['urs_user_already_logged', 'uat_urs_user_already_logged']

ERROR_REPORTING_ENDPOINT = 'search-error-report.asf.alaska.edu'
