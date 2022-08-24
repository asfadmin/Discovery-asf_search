import logging
from typing import Dict, List
from jinja2 import Environment, PackageLoader
from asf_search import ASFProduct

def get_additional_metalink_fields(_: ASFProduct):
    return {}


def ASFSearchResults_to_metalink(products: List[Dict]):
    logging.debug('translating: metalink')

    templateEnv = Environment(
        loader=PackageLoader('asf_search.export', 'templates'),
        autoescape=True
    )

    template = templateEnv.get_template('template.metalink')
    for line in template.stream(results=products):
        yield line
