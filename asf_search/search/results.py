from .product import ASFProduct

class ASFSearchResults(dict):
    def __init__(self, results: dict):
        super(ASFSearchResults, self).__init__(results)
        for index, product in enumerate(self['features']):
            self['features'][index] = ASFProduct(self['features'][index])

    def download_all(self, dir: str):
        for product in self['features']:
            product.download(dir=dir)
