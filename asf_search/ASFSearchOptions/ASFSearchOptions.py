from collections import UserDict
from .validator_map import validator_map

class ASFSearchOptions(UserDict):
    # Get's called for each item added to dict.
    # Make sure the thing added is a valid param:
    def __setitem__(self, key, value):
        if key not in validator_map:
            error_msg = f"Key '{key}' is not a valid search option."
            ## See if they just missed up case sensitivity:
            for valid_key in validator_map:
                if key.lower() == valid_key.lower():
                    error_msg += f" (Did you mean '{valid_key}'?)"
                    break
            raise KeyError(error_msg)
        # Run the value through the parser, before saving to the dict:
        self.data[key] = validator_map[key](value)
