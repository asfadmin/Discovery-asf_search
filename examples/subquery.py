"""
Simple example script showing a few basic uses of asf_search
"""

import asf_search as asf
import json
import logging
logging.basicConfig(level=logging.DEBUG)

glist = list(range(1, 5000))
opts = asf.ASFSearchOptions(granule_list='UA_bigsur_14067_21060_011_211020_L090_CX_01-SLOPE')
#opts = asf.ASFSearchOptions(granule_list='S1A_S3_RAW__0SDH_20140615T034443_20140615T034516_001055_00107C_BCD2-METADATA_RAW')

results = asf.search(opts=opts)
print(json.dumps(dict(opts), indent=2))
print('=========================')
print(results)
#logging.debug(opts)
#logging.debug(opts.granule_list)
#logging.debug(dict(opts))

#sub_queries = asf.build_subqueries(opts)

#translated = asf.translate_opts(sub_queries[0])

print('done')