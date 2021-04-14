"""
Simple example script showing a few basic uses of asf_search
"""

import json
import asf_search as asf

print('='*80)
print('Constants')
print(f'asf.BEAMMODE.IW: {asf.BEAMMODE.IW}')
print(f'asf.POLARIZATION.HH_HV: {asf.POLARIZATION.HH_HV}')
print(f'asf.PLATFORM.SENTINEL1: {asf.PLATFORM.SENTINEL1}')

print('='*80)
print(f'Health check: {json.dumps(asf.health(), indent=2)}')

print('='*80)
results = asf.search(platform=[asf.PLATFORM.SENTINEL1], maxResults=2)
print(f'Basic search example: {json.dumps(results, indent=2)}')

print('='*80)
results = asf.granule_search(['ALPSRS279162400', 'ALPSRS279162200'])
print(f'Granule search example: {json.dumps(results, indent=2)}')

print('='*80)
results = asf.product_search(['ALAV2A279102730', 'ALAV2A279133150'])
print(f'Product search example: {json.dumps(results, indent=2)}')

print('='*80)
wkt = 'POLYGON((-135.7 58.2,-136.6 58.1,-135.8 56.9,-134.6 56.1,-134.9 58.0,-135.7 58.2))'
results = asf.geo_search(platform=[asf.PLATFORM.SENTINEL1], intersectsWith=wkt, maxResults=2)
print(f'Geographic search example: {json.dumps(results, indent=2)}')

print('='*80)
results = asf.search(
    platform=[asf.PLATFORM.SENTINEL1],
    frame=[100, 150, (200, 205)],
    relativeOrbit=[100, 105, (110, 115)],
    processingLevel=[asf.PRODUCT_TYPE.SLC])
print(f'Path/frame/platform/product type example: {json.dumps(results, indent=2)}')

print('='*80)
results = asf.stack_from_id('S1B_WV_SLC__1SSV_20210126T234925_20210126T235632_025332_030462_C733-SLC')
print(f'Baseline stack search example: {json.dumps(results, indent=2)}')

print('='*80)
wkt = 'POLYGON((-160 65,-150 65,-160 60,-150 60,-160 65))' # Self-intersecting bowtie
try:
    results = asf.geo_search(platform=[asf.PLATFORM.SENTINEL1], intersectsWith=wkt)
except asf.ASFSearch4xxError as e:
    print(f'Exception example: {e}')