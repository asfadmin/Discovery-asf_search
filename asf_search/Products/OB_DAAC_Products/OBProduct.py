from typing import Dict
from asf_search import ASFProduct
from asf_search.ASFSession import ASFSession


class OBProduct(ASFProduct):
    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession):
        super().__init__(args, session)
        keys = [*self.properties.keys()]
        for key in keys:
            if self.properties.get(key) is None:
                self.properties.pop(key)
