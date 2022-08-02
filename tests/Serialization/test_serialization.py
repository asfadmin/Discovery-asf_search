from asf_search import ASFProduct, ASFSearchResults
from asf_search.ASFSearchOptions.ASFSearchOptions import ASFSearchOptions

import os
import json



def run_test_serialization(product=None, results=None, opts=ASFSearchOptions()):
    if product is None:
        to_serialize = ASFSearchResults([json_to_product(prod) for prod in results])
    else:
        to_serialize = ASFSearchResults([json_to_product(product)])

    with open('serialized_product.json', 'w') as f:
        f.write(json.dumps({"results": to_serialize.geojson(), "opts": dict(opts)}))
        f.close()

    with open('serialized_product.json', 'r') as f:
        deserialized = json.loads(f.read())
        f.close()

    os.remove('serialized_product.json')
    
    deserialized_results = deserialized.get('results')
    deserialized_opts = deserialized.get('opts')

    for key, value in deserialized_opts.items():
        assert value == getattr(opts, key)

    for idx, original in enumerate(to_serialize):
        assert deserialized_results['features'][idx]['properties'] == original.properties
        assert deserialized_results['features'][idx]['geometry'] == original.geometry
    
    assert deserialized_results['type'] == 'FeatureCollection'


def json_to_product(product):
    output = ASFProduct()
    output.meta = product['meta']
    output.properties = product['properties']
    output.geometry = product['geometry']
    output.umm = product['umm']
    
    return output
