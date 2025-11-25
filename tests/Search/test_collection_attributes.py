from asf_search.ASFSession import ASFSession
from asf_search.search.collection_attributes import get_searchable_attributes


def run_test_collection_attributes(params: dict, expected_attributes: list[str], session: ASFSession) -> None:
    actual_attributes = get_searchable_attributes(**params, session=session)

    assert sorted(expected_attributes) == sorted(actual_attributes.keys())
