from asf_search import search


class ASFCollection:
    def __init__(self, platform: str, mission: str):
        self.platform = platform
        self.mission = mission
    
    def search_collection(self, **args):
        return search(collectionName=self.mission, **args)
