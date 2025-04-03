class ASFError(Exception):
    """Base ASF Exception, not intended for direct use"""


class ASFSearchError(ASFError):
    """Base search-related Exception"""

class ASFGroupError(ASFError):
    """Base search-related Exception"""

class ASFNetworkError(ASFError):
    """Base search-related Exception"""

class ASFSearch4xxError(ASFSearchError):
    """Raise when CMR returns a 4xx error"""


class ASFSearch5xxError(ASFSearchError):
    """Raise when CMR returns a 5xx error"""


class ASFBaselineError(ASFSearchError):
    """Raise when baseline related errors occur"""


class ASFDownloadError(ASFError):
    """Base download-related Exception"""


class ASFAuthenticationError(ASFError):
    """Base download-related Exception"""


class ASFWKTError(ASFError):
    """Raise when wkt related errors occur"""


class CMRError(Exception):
    """Base CMR Exception"""


class CMRConceptIDError(CMRError):
    """Raise when CMR encounters a concept-id error"""


class CMRIncompleteError(CMRError):
    """Raise when CMR returns an incomplete page of results"""
