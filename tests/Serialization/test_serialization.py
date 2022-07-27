from typing import List
from asf_search import ASFProduct, ASFSearchResults
import json


def run_test_serialization(product=None, results=None):
    if product is None:
        to_serialize = ASFSearchResults([ASFProduct(prod) for prod in results])
    else:
        to_serialize = ASFSearchResults([ASFProduct(product)])

    if not to_serialize is None:
        with open('serialized_product.json', 'w') as f:
            f.write(json.dumps([{'umm': x.umm, 'meta': x.meta} for x in to_serialize]))
            f.close()

        with open('serialized_product.json', 'r') as f:
            deserialized = json.loads(f.read())
            deserialized = ASFSearchResults([ASFProduct(prod) for prod in deserialized])

            f.close()

    for idx, original in enumerate(to_serialize):
        assert deserialized[idx].properties == original.properties
        assert deserialized[idx].geometry == original.geometry
        assert deserialized[idx].meta == original.meta
        assert deserialized[idx].umm == original.umm
