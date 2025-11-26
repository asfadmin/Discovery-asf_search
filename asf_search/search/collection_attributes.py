from dataclasses import dataclass
from typing import Optional
from asf_search.CMR.datasets import collections_by_processing_level
from asf_search.ASFSession import ASFSession

from asf_search.exceptions import ASFSearchError, CMRError


@dataclass(frozen=True)
class AdditionalAttribute:
    """Wrapper dataclass around CMR Additional Attributes"""

    name: str
    """The `Name` of the additional attribute in CMR"""
    data_type: str
    """The `DataType` of the additional attribute in CMR"""
    description: str
    """The `Description` of the additional attribute in CMR"""


def get_searchable_attributes(
    shortName: Optional[str] = None,
    conceptID: Optional[str] = None,
    processingLevel: Optional[str] = None,
    session: ASFSession = ASFSession(),
) -> dict[str, AdditionalAttribute]:
    """Using a provided processingLevel, collection shortName, or conceptID query CMR's `/collections` endpoint and
    return a dictionary of additional attributes mapping the attribute's name to the additional attribute entry in CMR

    ``` python
    from pprint import pp
    SLCRcord = asf.get_searchable_attributes(processingLevel='SLC')
    pp(SLCRcord.additionalAttributes)
    ```
    """
    query_data = None
    method = None

    if shortName is not None:
        method = {'type': 'shortName', 'value': shortName}
        query_data = [('shortName', shortName)]
    elif conceptID is not None:
        query_data = [('concept-id', conceptID)]
        method = {'type': 'conceptID', 'value': conceptID}
    elif processingLevel is not None:
        method = {'type': 'processingLevel', 'value': processingLevel}
        query_data = _get_concept_ids_for_processing_level(processingLevel)
    else:
        raise ValueError(
            'Error: `get_collection_searchable_attributes()` expects `shortName`, `conceptID`, or `processingLevel`'
        )

    cmr_response = _query_cmr(session=session, query_data=query_data, method=method)

    if 'errors' in cmr_response:
        raise ValueError(f"CMR responded with an error. Original error(s): {' '.join(cmr_response['errors'])}")
    if len(cmr_response['items']) == 0:
        raise ValueError(
            f'Error: no collections found in CMR for given parameter `{method["type"]}`: "{method["value"]}" '
        )

    additionalAttributes = {}

    for entry in cmr_response['items']:
        umm = entry['umm']
        attributes = umm.get('AdditionalAttributes')
        if attributes is not None:
            for attribute in attributes:
                additionalAttributes[attribute.get('Name')] = AdditionalAttribute(
                    name=attribute.get('Name'),
                    description=attribute.get('Description'),
                    data_type=attribute.get('DataType'),
                )

    return additionalAttributes


def _get_concept_ids_for_processing_level(processing_level: str):
    collections = collections_by_processing_level.get(processing_level)
    if collections is None:
        raise ValueError(f'asf-search is missing concept-id aliases for processing level "{processing_level}". Please use `shortName` or `conceptID')
    return [('concept-id[]', collection) for collection in collections]


def _query_cmr(session: ASFSession, query_data: list[tuple[str, str]], method: dict) -> dict:
    url = 'https://cmr.earthdata.nasa.gov/search/collections.umm_json'

    response = session.post(url=url, data=query_data)

    try:
        return response.json()
    except Exception as exc:
        raise ASFSearchError(
            f'Failed to find collection attributes for {method["type"]} "{method["value"]}". original exception: {str(exc)}'
        )
