import json
import asf_search as asf

print(f'asf.DATASET.AVNIR: {asf.DATASET.AVNIR}')
print(f'asf.BEAMMODE.IW: {asf.BEAMMODE.IW}')
print(f'asf.POLARIZATION.HH_HV: {asf.POLARIZATION.HH_HV}')
print(f'asf.PLATFORM.SENTINEL1: {asf.PLATFORM.SENTINEL1}')
print(f'Health check: {json.dumps(asf.health(), indent=2)}')