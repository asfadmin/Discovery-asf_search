from .validator_map import validator_map, validate


class ASFSearchOptions:
    def __init__(self, **kwargs):
        # init the built in attrs:
        for key in validator_map.keys():
            self.__setattr__(key, None)
        
        # Apply any parameters passed in:
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def __setattr__(self, key, value):
        # self.* calls custom __setattr__ method, creating inf loop. Use super().*
        # Let values always be None, even if their validator doesn't agree. Used to delete them too:
        if value is None:
            super().__setattr__(key, None)
        elif key in validator_map:
            super().__setattr__(key, validate(key, value))
        else:
            raise KeyError(f"key '{key}' is not a valid search option (setattr)")

    def __delattr__(self, item):
        # If the attr is one of ours, just set it to None. Else remove whatever the user did:
        if item in validator_map:
            self.__setattr__(item, None)
        else:
            raise KeyError(f"key '{item}' is not a valid search option (delattr)")

    def __iter__(self):
        """
        Filters search parameters, only returning populated fields. Used when casting to a dict.
        """
        for key in validator_map:
            value = self.__getattribute__(key)
            if value is not None:
                yield key, value
