from collections import UserDict
from .validator_map import validator_map

class ASFSearchOptions(UserDict):
    # Get's called for each item added to dict.
    # Make sure the thing added is a valid param:
    def __setitem__(self, key, value):
        # Do we want to always modify their key? Or just
        # when comparing to validator map?
        key = key.lower()
        if key not in validator_map:
            raise KeyError(f"Key {key} is not a valid search option")
        # Run the value through the parser, before saving to the dict:
        self.data[key] = validator_map[key](value)
