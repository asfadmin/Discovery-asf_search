from asf_search.CMR.datasets import collections_by_processing_level
from asf_search.ASFSession import ASFSession
from asf_search.ASFSearchOptions import validators
from asf_search.exceptions import ASFSearchError
class SearchablAdditionalAttribute():
    name: str
    description: str
    dataType: str
    def __init__(self, attribute: dict) -> None:
        self.name = attribute.get('Name', '')
        self.description = attribute.get('Description', '')
        self.dataType = attribute.get('DataType', '')
        pass

    def __repr__(self) -> str:
        return f'{self.name} ({self.dataType}): {self.description}'
    
    def as_search_param(self, value) -> tuple[str, str]:
        cmr_value = value
        match self.dataType:
            case 'STRING':
                cmr_value = validators.parse_string(value)
            case 'INT':
                cmr_value =validators.parse_int(value)
            case 'FLOAT':
                cmr_value = validators.parse_float(value)
            case 'DATETIME_STRING':
                cmr_value = validators.parse_date(value)
        
        return ('attribute[]', f'{self.dataType.lower()},{self.name},{cmr_value}')

def get_collection_searchable_attributes(processing_level: str, session: ASFSession = ASFSession()) -> dict[str, SearchablAdditionalAttribute]:

    concept_ids = _get_concept_ids_for_processing_level(processing_level)
    cmr_response = _query_cmr(session, concept_ids)

    umm = cmr_response['items'][0]['umm']

    return additional_attributes_to_searchable(umm['AdditionalAttributes'])
 

def _get_concept_ids_for_processing_level(processing_level: str):
    collections = collections_by_processing_level.get(processing_level, [])
    return [('concept-id[]', collection) for collection in collections]
    
def _query_cmr(session: ASFSession, concept_ids: list[tuple[str, str]]) -> dict:
    url = 'https://cmr.earthdata.nasa.gov/search/collections.umm_json'
    
    response = session.post(url=url, data=concept_ids)

    try:
        return response.json()
    except Exception as exc:
        raise ASFSearchError(f'Failed to find collection attributes for processing level. original exception: {str(exc)}')

def additional_attributes_to_searchable(additional_attributes: list[dict]) -> dict[str, SearchablAdditionalAttribute]:
    return {attribute['Name']: SearchablAdditionalAttribute(attribute) for attribute in additional_attributes}
