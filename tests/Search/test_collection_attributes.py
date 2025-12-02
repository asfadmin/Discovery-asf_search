from asf_search.ASFSession import ASFSession
from asf_search.search.collection_attributes import get_searchable_attributes
import pytest

def run_test_collection_attributes(params: dict, expected_attributes: list[str], session: ASFSession, expect_failure: bool) -> None:
    if expect_failure:
        with pytest.raises(ValueError):
            actual_attributes = get_searchable_attributes(**params, session=session)
    else:
        actual_attributes = get_searchable_attributes(**params, session=session)
        assert sorted(expected_attributes) == sorted(actual_attributes.keys())
