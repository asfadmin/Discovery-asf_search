from .validator_map import validator_map, validate
from .defaults import defaults
from asf_search import ASFSession
from asf_search.constants import INTERNAL


class ASFSearchOptions:
    def __init__(self, **kwargs):
        """
        Initialize the object, creating the list of attributes based on the contents of validator_map, and assign them based on kwargs

        :param kwargs: any search options to be set immediately
        """
        # init the built in attrs:
        for key in validator_map.keys():
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
            if value is None:  # always maintain defaults on required fields
                if key in defaults:
                    super().__setattr__(key, defaults[key])
                else:
                    super().__setattr__(key, None)
            else:
                super().__setattr__(key, validate(key, value))
        else:
            raise KeyError(f"key '{key}' is not a valid search option (setattr)")

    def __delattr__(self, item):
        """
        Clear a search option by setting its value to None

        :param item: the name of the option to clear
        """
        if item in validator_map:
            self.__setattr__(item, None)
        else:
            raise KeyError(f"key '{item}' is not a valid search option (delattr)")

    def __iter__(self):
        """
        Filters search parameters, only returning populated fields. Used when casting to a dict.
        """
        no_export = ['host', 'session', 'provider', 'maturity']  # TODO: remove 'provider' from this list once we're hitting CMR directly
        for key in validator_map:
            if key not in no_export:
                value = self.__getattribute__(key)
                if value is not None:
                    yield key, value

    def reset(self):
        """
        Resets all populated search options, exlcuding options that have defined defaults in defaults.py unchanged (host, session, etc)
        """
        for key, _ in self:
            if key not in defaults.keys():
                super().__setattr__(key, None)
