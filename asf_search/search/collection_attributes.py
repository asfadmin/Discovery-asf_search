from typing import Optional
from asf_search.CMR.datasets import collections_by_processing_level
from asf_search.ASFSession import ASFSession

# from asf_search.ASFSearchOptions import validators
from asf_search.exceptions import ASFSearchError
from dataclasses import dataclass

@dataclass(frozen=True)
class AdditionalAttribute:
    """Dataclass wrapper for CMR additional attribute schema
    
    Properties:
    - name: str
    - description: str
    - dataType: str
    """
    name: str
    """Name of the attribute in CMR"""
    description: str
    """Description of the attribute in CMR"""
    dataType: str
    """Datatype of the attribute in CMR"""

    # def build_search_param(self, value) -> tuple[str, str]:
    #     """Generate the cmr search keyword with a given value. Pass output to `search()` with `cmr_keywords` param"""
    #     cmr_value = value
    #     match self.dataType:
    #         case 'STRING':
    #             cmr_value = validators.parse_string(value)
    #         case 'INT':
    #             cmr_value =validators.parse_int(value)
    #         case 'FLOAT':
    #             cmr_value = validators.parse_float(value)
    #         case 'DATETIME_STRING':
    #             cmr_value = validators.parse_date(value)

    #     return ('attribute[]', f'{self.dataType.lower()},{self.name},{cmr_value}')

@dataclass(frozen=True)
class CMRCollectionRecord:
    """Barebones dataclass reprsenting a CMR Collection record. Contains
    
    Properties:
    - shortName: str
    - conceptID: str
    - additionalAttributes: list[AdditionalAttribute]
    """
    shortName: str
    """Short name of CMR collection record is derived from"""
    conceptID: str
    """Collection concept-id of CMR collection record is derived from"""
    additionalAttributes: list[AdditionalAttribute]
    """Additional attributes defined in CMR collection record"""

    
def get_searchable_attributes(
    shortName: Optional[str] = None,
    conceptID: Optional[str] = None,
    processingLevel: Optional[str] = None,
    session: ASFSession = ASFSession(),
) -> CMRCollectionRecord:
    """Using a provided processingLevel, collection shortName, or conceptID query CMR's `/collections` endpoint and
    return `CMRCollectionRecord` for more readily searchable list of additional attributes
    
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

    if len(cmr_response['items']) == 0:
        raise ValueError(
            f'Error: no collections found in CMR for given parameter `{method["type"]}`: "{method["value"]}" '
        )
    entry = cmr_response['items'][0]
    umm = entry['umm']
    meta = entry['meta']

    entryShortName = umm['ShortName']
    entryConceptID = meta['concept-id']

    return _additional_attributes_to_CMRCollectionRecord(
        umm['AdditionalAttributes'], conceptID=entryConceptID, shortName=entryShortName
    )


def _get_concept_ids_for_processing_level(processing_level: str):
    collections = collections_by_processing_level.get(processing_level, [])
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


def _additional_attributes_to_CMRCollectionRecord(
    additional_attributes: list[dict], conceptID: str, shortName: str
) -> CMRCollectionRecord:
    """"""
    return CMRCollectionRecord(
        shortName=shortName,
        conceptID=conceptID,
        additionalAttributes=[AdditionalAttribute(
                name=attribute['Name'],
                description=attribute['Description'],
                dataType=attribute['DataType'],
            )
            for attribute in additional_attributes
        ],
    )
