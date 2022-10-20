import asf_search as asf
from datetime import date
import os
from pathlib import Path

download_files = True
path = os.getcwd()

USERNAME = ''
PASSWORD = ''

aoi = 'POLYGON((10.2134 43.957,10.2369 43.957,10.2369 43.9674,10.2134 43.9674,10.2134 43.957))'

opts = {
    'platform': asf.PLATFORM.SENTINEL1,
    'processingLevel': [asf.PRODUCT_TYPE.SLC],
    'relativeOrbit': 168,
    'start': date(2021, 6, 1),
    'end': date(2022, 1, 31),
    #'maxResults': 1
}

results = asf.geo_search(intersectsWith=aoi, **opts)
print(f'Total Images Found: {len(results)}')
print(results)

##### download bar works only if processes = 1:
if download_files == True:
    session = asf.ASFSession().auth_with_creds(USERNAME, PASSWORD)
    print("download in :",path)
    results.download(path = path, session = session, processes = 1 )
