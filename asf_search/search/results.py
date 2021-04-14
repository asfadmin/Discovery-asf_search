from .product import ASFProduct

class ASFSearchResults(dict):
    def __init__(self, results: dict):
        super(ASFSearchResults, self).__init__(results)
        for index, product in enumerate(self['features']):
            self['features'][index] = ASFProduct(self['features'][index])

    def download(self, dir: str, token: str = None) -> None:
        """
        Iterates over each ASFProduct and downloads them to the specified directory.

        :param dir: The directory into which the products should be downloaded.
        :param token: EDL authentication token for authenticated downloads, see https://urs.earthdata.nasa.gov/user_tokens

        :return: None
        """

        for product in self['features']:
            product.download(dir=dir, token=token)
