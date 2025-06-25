class ASFError(Exception):
    """Base ASF Exception, not intended for direct use"""


class ASFSearchError(ASFError):
    """Base search-related Exception"""

class ASFGroupError(ASFError):
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


class DateTypeError(ASFError):
    """Raise when a provided date format is unable to be parsed"""


class CoherenceEstimationError(ASFError):
    """Raise if coherence estimation is requested for a Pair with a temporal baseline > 48 days"""


class MultiBurstError(ASFError):
    """Base MultiBurst Exception, not intended  direct use"""


class InvalidMultiBurstCountError(MultiBurstError):
    """Raise when a MultiBurst dict contains too many or no bursts"""


class MultipleOrbitError(MultiBurstError):
    """Raise when a MultiBurst dict contains bursts in multiple oribital paths"""


class InvalidMultiBurstTopologyError(MultiBurstError):
    """Raise when a collection of bursts is disconnected or contains holes"""


class AntimeridianError(MultiBurstError):
    """Raise when a multiburst collection intersects the Antimeridian"""


class CMRError(Exception):
    """Base CMR Exception"""


class CMRConceptIDError(CMRError):
    """Raise when CMR encounters a concept-id error"""


class CMRIncompleteError(CMRError):
    """Raise when CMR returns an incomplete page of results"""
