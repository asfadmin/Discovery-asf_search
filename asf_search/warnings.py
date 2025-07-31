class ASFWarning(Warning):
    """
    Base ASF Warning, not intended for direct use

    Tip: Silence me to silence all child ASFWarnings
    """


class PairNotInFullStackWarning(ASFWarning):
    """Warn when attempting to do something with a Pair that is not in Stack.full_stack"""


class OptionalDependencyWarning(ASFWarning):
    """Warn when an optional dependency is not installed in the user environment"""

