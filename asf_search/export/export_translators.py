from types import FunctionType
from datetime import datetime

from asf_search import ASFSearchResults
from .csv import ASFSearchResults_to_csv, get_additional_csv_fields
from .kml import ASFSearchResults_to_kml, get_additional_kml_fields
from .metalink import get_additional_metalink_fields, ASFSearchResults_to_metalink
from .jsonlite import get_additional_jsonlite_fields, ASFSearchResults_to_jsonlite
from .jsonlite2 import ASFSearchResults_to_jsonlite2

def output_translators():
    return {
        'csv':          results_to_format(get_additional_csv_fields, ASFSearchResults_to_csv),
        'kml':          results_to_format(get_additional_kml_fields, ASFSearchResults_to_kml),
        'metalink':     results_to_format(get_additional_metalink_fields, ASFSearchResults_to_metalink),
        'jsonlite':     results_to_format(get_additional_jsonlite_fields, ASFSearchResults_to_jsonlite),
        'jsonlite2':     results_to_format(get_additional_jsonlite_fields, ASFSearchResults_to_jsonlite2),
    }

def results_to_format(get_additional_fields: FunctionType, to_export_format: FunctionType):
    return lambda results: to_export_format(ASFSearchResults_to_properties_list(results, get_additional_fields))

# ASFProduct.properties don't have every property required of certain output formats, 
# This grabs the missing properties from ASFProduct.umm required by the given format
def ASFSearchResults_to_properties_list(results: ASFSearchResults, get_additional_fields: FunctionType):
    property_list = []
    
    for product in results:
        additional_fields = get_additional_fields(product)
        properties = {**product.properties, **additional_fields}
        property_list.append(properties)
    
    # Format dates to match format used by SearchAPI output formats
    for product in property_list:
        # S1 date properties are formatted differently from other platforms
        is_S1 = product['platform'].upper() in ['SENTINEL-1', 'SENTINEL-1B', 'SENTINEL-1A']
        for key, data in product.items():
            if ('date' in key.lower() or 'time' in key.lower()) and data is not None:
                if is_S1:
                    time = datetime.strptime(data[:-1], '%Y-%m-%dT%H:%M:%S.%f')
                    product[key] = time.strftime('%Y-%m-%dT%H:%M:%S.%f')
                else:
                    # Remove trailing zeroes from miliseconds, add Z
                    if len(data.split('.')) == 2:
                        d = len(data.split('.')[0])
                        data = data[:d] + 'Z'
                    time = datetime.strptime(data, '%Y-%m-%dT%H:%M:%SZ')
                    product[key] = time.strftime('%Y-%m-%dT%H:%M:%SZ')

    return property_list
