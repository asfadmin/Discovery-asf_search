from asf_search.exceptions import ASFDownloadError
import os.path

class ASFProduct(dict):
    def download(self, dir: str, filename: str = None):
        if filename is None:
            filename = self['properties']['fileName']

        if not os.path.isdir(dir):
            raise ASFDownloadError(f'Error downloading {self["properties"]["fileID"]}: directory not found: {dir}')

        if os.path.isfile(os.path.join(dir, filename)):
            raise ASFDownloadError(f'File already exists: {os.path.join(dir, filename)}')

        print("I totally downloaded the file just now")

    def stack(self):
        pass