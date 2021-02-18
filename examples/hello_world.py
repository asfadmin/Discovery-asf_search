import json
import asf_search as asf

print(asf.DATASET.AVNIR)
print(asf.BEAMMODE.IW)
print(asf.POLARIZATION.HH_HV)
print(asf.PLATFORM.SENTINEL1)
print(f'https://{asf.INTERNAL.HOST}{asf.INTERNAL.HEALTH_PATH}')
print(json.dumps(asf.health(), indent=2))