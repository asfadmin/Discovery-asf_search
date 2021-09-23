from collections import UserDict
from .validator_map import validator_map, validate


class ASFSearchOptions:
    def __init__(self, **args):
        super().__setattr__('keywords', validator_map.keys())
        for key in self.keywords:
            self.__setattr__(key, None)
        if self.provider is None:
            self.provider = 'ASF'


    def __setattr__(self, key, value):
        if value is None:
            super().__setattr__(key, None)
        else:
            super().__setattr__(key, validate(key, value))

    def __delattr__(self, item):
        self.__setattr__(item, None)

    def __iter__(self):
        """
        Filters search parameters, only returning populated fields. Used when casting to a pruned dict.
        :return:
        """
        for key in self.keywords:
            value = self.__getattribute__(key)
            if value is not None:
                yield key, self.__getattribute__(key)
