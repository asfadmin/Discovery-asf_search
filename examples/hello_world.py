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
print(f'Basic search example: {results}')

print('='*80)
results = asf.granule_search(['ALPSRS279162400', 'ALPSRS279162200'])
print(f'Granule search example: {results}')

print('='*80)
results = asf.product_search(['ALAV2A279102730', 'ALAV2A279133150'])
print(f'Product search example: {results}')

print('='*80)
wkt = 'POLYGON((-135.7 58.2,-136.6 58.1,-135.8 56.9,-134.6 56.1,-134.9 58.0,-135.7 58.2))'
results = asf.geo_search(platform=[asf.PLATFORM.SENTINEL1], intersectsWith=wkt, maxResults=2)
print(f'Geographic search example: {results}')

print('='*80)
results = asf.search(
    platform=[asf.PLATFORM.SENTINEL1],
    frame=[100, 150, (200, 205)],
    relativeOrbit=[100, 105, (110, 115)],
    processingLevel=[asf.PRODUCT_TYPE.SLC])
print(f'Path/frame/platform/product type example: {results}')

print('='*80)
results = asf.stack_from_id('S1B_WV_SLC__1SSV_20210126T234925_20210126T235632_025332_030462_C733-SLC')
print(f'Baseline stack search example, ephemeris-based: {results}')

print('='*80)
try:
    results = asf.stack_from_id('nonexistent-scene')
except asf.ASFSearchError as e:
    print(f'Stacking a non-existent scene throws an exception: {e}')

print('='*80)
try:
    results = asf.stack_from_id('UA_atchaf_06309_21024_020_210401_L090_CX_01-PROJECTED')
except asf.ASFBaselineError as e:
    print(f'Not everything can be stacked: {e}')

print('='*80)
results = asf.stack_from_id('ALPSRP279071390-RTC_HI_RES')
print(f'Baseline stack search example, pre-calculated: {results}')

print('='*80)
results = results[0].stack()
print(f'Baseline stacks can also be made from an ASFProduct: {results}')

print('='*80)
print(f'ASFSearchResults work like lists: {results[3:5]}')

print('='*80)
print(f'ASFSearchResults serializes to geojson: {results[3:5]}')

print('='*80)
product = results[2]
print(f'ASFProduct serializes to geojson: {product}')


print('='*80)
wkt = 'POLYGON((-160 65,-150 65,-160 60,-150 60,-160 65))' # Self-intersecting bowtie
try:
    results = asf.geo_search(platform=[asf.PLATFORM.SENTINEL1], intersectsWith=wkt)
except asf.ASFWKTError as e:
    print(f'Exception example: {e}')

print('='*80)
print('A few more exception examples:')
try:
    asf.search(offNadirAngle=[tuple([1])])
except ValueError as e:
    print(f'Tuple too short: {e}')
try:
    asf.search(offNadirAngle=[(1, 2, 3)])
except ValueError as e:
    print(f'Tuple too long: {e}')
try:
    asf.search(offNadirAngle=[('a', 2)])
except ValueError as e:
    print(f'Tuple non-numeric min: {e}')
try:
    asf.search(offNadirAngle=[(1, 'b')])
except ValueError as e:
    print(f'Tuple non-numeric max: {e}')
try:
    asf.search(offNadirAngle=[(float("NaN"), 2)])
except ValueError as e:
    print(f'Tuple non-finite min: {e}')
try:
    asf.search(offNadirAngle=[1, (float("Inf"))])
except ValueError as e:
    print(f'Tuple non-finite max: {e}')
try:
    asf.search(offNadirAngle=[(2, 1)])
except ValueError as e:
    print(f'Tuple min > max: {e}')
try:
    asf.search(offNadirAngle=[float("Inf")])
except ValueError as e:
    print(f'Bare value non-finite: {e}')
try:
    asf.search(offNadirAngle=['a'])
except ValueError as e:
    print(f'Bare value non-numeric: {e}')
