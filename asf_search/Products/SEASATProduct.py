from typing import Dict
from asf_search import ASFSession, ASFProduct
from asf_search.CMR.translate import try_parse_int, try_round_float


class SEASATProduct(ASFProduct):
    """
    ASF Dataset Documentation Page: https://asf.alaska.edu/data-sets/sar-data-sets/seasat/
    """

    _base_properties = {
        **ASFProduct._base_properties,
        'md5sum': {'path': ['AdditionalAttributes', ('Name', 'MD5SUM'), 'Values', 0]},
        'frameNumber': {'path': ['AdditionalAttributes', ('Name', 'FRAME_NUMBER'), 'Values', 0], 'cast': try_parse_int}, # for consolidated collection
        'bytes': {'path': ['DataGranule', 'ArchiveAndDistributionInformation']},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        bytes_mapping = {
            entry['Name']: {'bytes': entry['SizeInBytes'], 'format': entry['Format']}
            for entry in self.properties['bytes']
        }
        md5sum_mapping = {
            entry['Name']: entry['Checksum']['Value']
            for entry in self.properties['bytes']
        }

        self.properties['bytes'] = bytes_mapping
        self.properties['md5sum'] = md5sum_mapping

        self.properties['additionalUrls'] = self._get_additional_urls()
        self.properties['browse'] = [url for url in self._get_urls() if url.endswith('.png') or url.endswith('.jpg') or url.endswith('.jpeg')]
        self.properties['s3Urls'] = self._get_s3_uris()

        center = self.centroid()
        self.properties['centerLat'] = center.y
        self.properties['centerLon'] = center.x
