from typing import Dict
from asf_search import ASFProduct, ASFSession


class UAVSARProduct(ASFProduct):
    """
    ASF Dataset Documentation Page: https://asf.alaska.edu/datasets/daac/uavsar/
    """

    _base_properties = {
        **ASFProduct._base_properties,
        'groupID': {'path': ['AdditionalAttributes', ('Name', 'GROUP_ID'), 'Values', 0]},
        'insarStackId': {'path': ['AdditionalAttributes', ('Name', 'INSAR_STACK_ID'), 'Values', 0]},
        'processingLevel': {
            'path': ['AdditionalAttributes', ('Name', 'PRODUCT_TYPE'), 'Values', 0]
        },
        'polarization': {
            'path': ['AdditionalAttributes', ('Name', 'POLARIZATION'), 'Values']
        },  # for consolidated collection
        'bytes': {'path': ['DataGranule', 'ArchiveAndDistributionInformation']},
    }

    def __init__(self, args: Dict = {}, session: ASFSession = ASFSession()):
        super().__init__(args, session)

        bytes_mapping = {
            entry['Name']: {'bytes': entry['SizeInBytes'], 'format': entry['Format']}
            for entry in self.properties['bytes']
        }
        md5sum_mapping = {
            entry['Name']: entry['Checksum']['Value'] for entry in self.properties['bytes']
        }

        self.properties['bytes'] = bytes_mapping
        self.properties['md5sum'] = md5sum_mapping

        self.properties['additionalUrls'] = self._get_additional_urls()
        self.properties['browse'] = [
            url
            for url in self._get_urls()
            if url.endswith('.png') or url.endswith('.jpg') or url.endswith('.jpeg')
        ]
        self.properties['s3Urls'] = self._get_s3_uris()

        center = self.centroid()
        self.properties['centerLat'] = center.y
        self.properties['centerLon'] = center.x

        # TODO: Drop this if/when UMM metadata updated with platform
        self.properties['platform'] = 'UAVSAR'
