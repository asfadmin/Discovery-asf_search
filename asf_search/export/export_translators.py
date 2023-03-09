from types import FunctionType
from datetime import datetime

from asf_search import ASFSearchResults

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
