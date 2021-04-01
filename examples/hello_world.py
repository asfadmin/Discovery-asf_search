"""
Simple example script showing a few basic uses of asf_search
"""

import json
import asf_search as asf

print('='*80)
print('Constants')
print(f'asf.DATASET.AVNIR: {asf.DATASET.SENTINEL1}')
print(f'asf.BEAMMODE.IW: {asf.BEAMMODE.IW}')
print(f'asf.POLARIZATION.HH_HV: {asf.POLARIZATION.HH_HV}')
print(f'asf.PLATFORM.SENTINEL1: {asf.PLATFORM.SENTINEL1}')

print('='*80)
print(f'Health check: {json.dumps(asf.health(), indent=2)}')

print('='*80)
results = asf.search(platform=[asf.PLATFORM.SENTINEL1], maxResults=2)
print(f'Basic search check: {json.dumps(results, indent=2)}')

print('='*80)
results = asf.granule_search(['ALPSRS279162400', 'ALPSRS279162200'])
print(f'Granule search check: {json.dumps(results, indent=2)}')

print('='*80)
results = asf.product_search(['ALAV2A279102730', 'ALAV2A279133150'])
print(f'Product search check: {json.dumps(results, indent=2)}')

print('='*80)
wkt = 'POLYGON((-135.7843 58.2625,-136.6521 58.1589,-135.8928 56.9884,-134.6724 56.1857,-134.9571 58.0335,-135.7843 58.2625))'
results = asf.geo_search(platform=[asf.PLATFORM.SENTINEL1], intersectsWith=wkt, maxResults=2)
print(f'Geographic search check: {json.dumps(results, indent=2)}')

print('='*80)
results = asf.stack('S1B_WV_SLC__1SSV_20210126T234925_20210126T235632_025332_030462_C733-SLC')
print(f'Baseline stack check: {json.dumps(results, indent=2)}')
