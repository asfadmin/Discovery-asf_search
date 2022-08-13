# from .count import count, req_fields_count
from .csv import ASFSearchResults_to_csv
# from .download import cmr_to_download, req_fields_download
# from .geojson import cmr_to_geojson, req_fields_geojson
# from .json import cmr_to_json, req_fields_json
# from .jsonlite import cmr_to_jsonlite, req_fields_jsonlite
# from .jsonlite2 import cmr_to_jsonlite2, req_fields_jsonlite2
# from .kml import cmr_to_kml, req_fields_kml
# from .metalink import cmr_to_metalink, req_fields_metalink

def output_translators():
    return {
        'csv':          [ASFSearchResults_to_csv, 'text/csv; charset=utf-8', 'csv'],
    }
