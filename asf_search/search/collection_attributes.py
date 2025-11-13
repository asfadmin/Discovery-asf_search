from asf_search.CMR.datasets import collections_by_processing_level
from asf_search.ASFSession import ASFSession

def get_collection_searchable_attributes(processing_level: str, session: ASFSession = ASFSession()) -> dict:
    collections = collections_by_processing_level.get(processing_level, [])
    concept_ids = [('concept-id[]', collection) for collection in collections]
    
    url = 'https://cmr.earthdata.nasa.gov/search/collections.umm_json'
    
    response = session.post(url=url, data=concept_ids)
    return response.json()
