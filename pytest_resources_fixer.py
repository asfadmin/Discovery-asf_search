import json
from typing import List
import asf_search as asf
import os
from pathlib import Path
import yaml

def load_yml(yml_file: str):
    if not yml_file.path.endswith('.yml') and not yml_file.path.endswith('.yaml'):
        return None
    with open(Path(base_path, yml_file), 'r') as f:
        try:
            resp = yaml.safe_load(f)
            f.close()
            return resp
        except yaml.YAMLError as exc:
            print(exc)
    
    print(f'failed to load {yml_file}')
    return None
            
def write_yml(yml_file: str, data):
    # if not yml_file.path.endswith('.yml') and not yml_file.path.endswith('.yaml'):
    #     return None
    with open(Path(base_path, yml_file), 'w') as f:
        f.write(json.dumps(data, indent=4))
        # yaml.safe_dump(data, f)
        f.close()
        # try:
        #     resp = yaml.safe_load(f)
        #     f.close()
        #     return resp
        # except yaml.YAMLError as exc:
        #     print(exc)
    
    # print(f'failed to load {yml_file}')
    # return None

working_dir = os.getcwd()
relative_path = "tests/yml_tests/Resources"

base_path = Path(working_dir, relative_path)

# for yml_file in os.scandir(base_path):
#     res = load_yml(yml_file)
    
#     if res == None:
#         continue
    
#     granules_to_update = []
#     if isinstance(res, List):
#         if res[0].get('properties', False):
#             granules_to_update.extend([granule['properties'].get('fileID') for granule in res])
#     elif res.get('properties', False):
#         granules_to_update.extend([res['properties'].get('fileID')])
#     else:
#         continue

s1_response = ['S1A_S3_RAW__0SDH_20140615T034443_20140615T034516_001055_00107C_BCD2-METADATA_RAW', 'S1B_IW_GRDH_1SDV_20211110T032039_20211110T032104_029520_0385E6_60DB-GRD_HD']
    # print(yml_file.name)
    # print(granules_to_update)
granule_search = asf.product_search(product_list=s1_response)

data = [{
    'type': 'Feature', 
    'geometry': product.geometry, 
    'properties': product.properties,
    'baseline': product.baseline,
    'umm': product.umm,
    'meta': product.meta
    } for product in granule_search]

if len(data) == 1:
    data = data[0]

write_yml('S1_response.yml', data)
# break