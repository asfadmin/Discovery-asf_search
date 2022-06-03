from asf_search.constants import INTERNAL
from asf_search.ASFSession import ASFSession

defaults = {
    'host': INTERNAL.CMR_HOST,
    'provider': INTERNAL.DEFAULT_PROVIDER,
    'session': ASFSession(),
    'maturity': None
}
