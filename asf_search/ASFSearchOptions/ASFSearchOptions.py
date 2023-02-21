import warnings
import json

from .validator_map import validator_map, validate
from .config import config
from asf_search import ASF_LOGGER

class ASFSearchOptions:
    def __init__(self, **kwargs):
        """
        Initialize the object, creating the list of attributes based on the contents of validator_map, and assign them based on kwargs

        :param kwargs: any search options to be set immediately
        """
        # init the built in attrs:
        for key in validator_map:
            self.__setattr__(key, None)
        
        # Apply any parameters passed in:
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def __setattr__(self, key, value):
        """
        Set a search option, restricting to the keys in validator_map only, and applying validation to the value before setting
        
        :param key: the name of the option to be set
        :param value: the value to which to set the named option
        """
        # self.* calls custom __setattr__ method, creating inf loop. Use super().*
        # Let values always be None, even if their validator doesn't agree. Used to delete them too:
        if key in validator_map:
            if value is None:  # always maintain config on required fields
                if key in config:
                    super().__setattr__(key, config[key])
                else:
                    super().__setattr__(key, None)
            else:
                super().__setattr__(key, validate(key, value))
        else:
            msg = f"key '{key}' is not a valid search option (setattr)"
            ASF_LOGGER.error(msg)
            raise KeyError(msg)

    def __delattr__(self, item):
        """
        Clear a search option by setting its value to None

        :param item: the name of the option to clear
        """
        if item in validator_map:
            self.__setattr__(item, None)
        else:
            msg = f"key '{item}' is not a valid search option (delattr)"
            ASF_LOGGER.error(msg)
            raise KeyError(msg)

    def __iter__(self):
        """
        Filters search parameters, only returning populated fields. Used when casting to a dict.
        """

        for key in validator_map:
            if not self._is_val_default(key):
                value = self.__getattribute__(key)
                yield key, value

    def __str__(self):
        """
        What to display if `print(opts)` is called.
        """
        return json.dumps(dict(self), indent=4)

    # Default is set to '...', since 'None' is a very valid value here
    def pop(self, key, default=...):
        """
        Removes 'key' from self and returns it's value. Throws KeyError if doesn't exist

        :param key: name of key to return value of, and delete
        """
        if key not in validator_map:
            msg = f"key '{key}' is not a valid key for ASFSearchOptions. (pop)"
            ASF_LOGGER.error(msg)
            raise KeyError(msg)

        if self._is_val_default(key):
            if default != ...:
                return default
            msg = f"key '{key}' is set to empty/None. (pop)"
            ASF_LOGGER.error(msg)
            raise KeyError(msg)

        # Success, delete and return it:
        val = getattr(self, key)
        self.__delattr__(key)
        return val

    def reset_search(self):
        """
        Resets all populated search options, excluding config options (host, session, etc)
        """
        for key, _ in self:
            if key not in config:
                super().__setattr__(key, None)

    def merge_args(self, **kwargs) -> None:
        """
        Merges all keyword args into this ASFSearchOptions object. Emits a warning for any options that are over-written by the operation.

        :param kwargs: The search options to merge into the object
        :return: None
        """
        for key in kwargs:
            # Spit out warning if the value is something other than the default:
            if not self._is_val_default(key):
                msg = f'While merging search options, existing option {key}:{getattr(self, key, None)} overwritten by kwarg with value {kwargs[key]}'
                ASF_LOGGER.warging(msg)
                warnings.warn(msg)
            self.__setattr__(key, kwargs[key])

    def _is_val_default(self, key) -> bool:
        """
        Returns bool on if the key's current value is the same as it's default value

        :param key: The key to check
        :return: bool
        """
        default_val = config[key] if key in config else None
        current_val = getattr(self, key, None)
        return current_val == default_val
