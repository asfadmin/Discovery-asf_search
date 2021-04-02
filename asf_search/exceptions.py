class ASFSearchError(Exception):
    """Base Exception for asf_search"""

class ASFSearch4xxError(ASFSearchError):
    """Raise when SearchAPI returns a 4xx error"""

class ASFSearch5xxError(ASFSearchError):
    """Raise when SearchAPI returns a 5xx error"""

class ServerError(ASFSearchError):
    """Raise when SearchAPI returns an unknown error"""