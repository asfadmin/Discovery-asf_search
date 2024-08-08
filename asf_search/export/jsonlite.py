import inspect
import json
from types import GeneratorType
from typing import Tuple
from shapely.geometry import shape
from shapely.ops import transform

from asf_search import ASF_LOGGER
from asf_search.export.export_translators import ASFSearchResults_to_properties_list

extra_jsonlite_fields = [
    (
        "processingTypeDisplay",
        ["AdditionalAttributes", ("Name", "PROCESSING_TYPE_DISPLAY"), "Values", 0],
    ),
    ("thumb", ["AdditionalAttributes", ("Name", "THUMBNAIL_URL"), "Values", 0]),
    (
        "faradayRotation",
        ["AdditionalAttributes", ("Name", "FARADAY_ROTATION"), "Values", 0],
    ),
    ("sizeMB", ["DataGranule", "ArchiveAndDistributionInformation", 0, "Size"]),
    ("flightLine", ["AdditionalAttributes", ("Name", "FLIGHT_LINE"), "Values", 0]),
    ("missionName", ["AdditionalAttributes", ("Name", "MISSION_NAME"), "Values", 0]),
]

def results_to_jsonlite(results):
    ASF_LOGGER.info('started translating results to jsonlite format')
    if len(results) == 0:
        yield from json.JSONEncoder(indent=2, sort_keys=True).iterencode({'results': []})
        return

    if not inspect.isgeneratorfunction(results) and not isinstance(results, GeneratorType):
        results = [results]

    streamer = JSONLiteStreamArray(results)
    jsondata = {"results": streamer}

    for p in json.JSONEncoder(indent=2, sort_keys=True).iterencode(jsondata):
        yield p


def unwrap_shape(x, y, z=None):
    x = x if x > 0 else x + 360
    return tuple([x, y])


def get_wkts(geometry) -> Tuple[str, str]:
    wrapped = shape(geometry)

    min_lon, max_lon = (wrapped.bounds[0], wrapped.bounds[2])

    if max_lon - min_lon > 180:
        unwrapped = transform(unwrap_shape, wrapped)
    else:
        unwrapped = wrapped

    return wrapped.wkt, unwrapped.wkt


class JSONLiteStreamArray(list):
    def __init__(self, results):
        self.results = results

        # need to make sure we actually have results so we can intelligently set __len__, otherwise
        # iterencode behaves strangely and will output invalid json
        self.len = 1

    def __iter__(self):
        return self.streamDicts()

    def __len__(self):
        return self.len

    def get_additional_output_fields(self, product):
        # umm = product.umm

        additional_fields = {}
        for key, path in extra_jsonlite_fields:
            additional_fields[key] = product.umm_get(product.umm, *path)

        if product.properties["platform"].upper() in [
            "ALOS",
            "RADARSAT-1",
            "JERS-1",
            "ERS-1",
            "ERS-2",
        ]:
            insarGrouping = product.umm_get(
                product.umm,
                *["AdditionalAttributes", ("Name", "INSAR_STACK_ID"), "Values", 0],
            )

            if insarGrouping not in [None, 0, "0", "NA", "NULL"]:
                additional_fields["canInsar"] = True
                additional_fields["insarStackSize"] = product.umm_get(
                    product.umm,
                    *[
                        "AdditionalAttributes",
                        ("Name", "INSAR_STACK_SIZE"),
                        "Values",
                        0,
                    ],
                )
            else:
                additional_fields["canInsar"] = False
        else:
            additional_fields["canInsar"] = product.baseline is not None

        additional_fields["geometry"] = product.geometry

        return additional_fields

    def streamDicts(self):
        completed = False
        for page_idx, page in enumerate(self.results):
            ASF_LOGGER.info(f"Streaming {len(page)} products from page {page_idx}")
            completed = page.searchComplete

            yield from [
                self.getItem(p)
                for p in ASFSearchResults_to_properties_list(
                    page, self.get_additional_output_fields
                )
                if p is not None
            ]

        if not completed:
            ASF_LOGGER.warn("Failed to download all results from CMR")

        ASF_LOGGER.info(f"Finished streaming {self.getOutputType()} results")

    def getItem(self, p):
        for i in p.keys():
            if p[i] == "NA" or p[i] == "":
                p[i] = None
        try:
            if p.get("offNadirAngle") is not None and float(p["offNadirAngle"]) < 0:
                p["offNadirAngle"] = None
        except TypeError:
            pass

        try:
            if p.get("patNumber"):
                if float(p["pathNumber"]) < 0:
                    p["pathNumber"] = None
        except TypeError:
            pass

        try:
            if p.get("groupID") is None:
                p["groupID"] = p["sceneName"]
        except TypeError:
            pass

        try:
            p["sizeMB"] = float(p["sizeMB"])
        except TypeError:
            pass

        try:
            p["pathNumber"] = int(p["pathNumber"])
        except TypeError:
            pass

        try:
            p['frameNumber'] = int(p.get('frameNumber'))
        except TypeError:
            pass

        try:
            p["orbit"] = int(p["orbit"])
        except TypeError:
            pass

        wrapped, unwrapped = get_wkts(p["geometry"])
        result = {
            "beamMode": p["beamModeType"],
            "browse": [] if p.get("browse") is None else p.get("browse"),
            "canInSAR": p.get("canInsar"),
            "dataset": p.get("platform"),
            "downloadUrl": p.get("url"),
            "faradayRotation": p.get("faradayRotation"),  # ALOS
            "fileName": p.get("fileName"),
            "flightDirection": p.get("flightDirection"),
            "flightLine": p.get("flightLine"),
            "frame": p.get("frameNumber"),
            "granuleName": p.get("sceneName"),
            "groupID": p.get("groupID"),
            "instrument": p.get("sensor"),
            "missionName": p.get("missionName"),
            "offNadirAngle": str(p["offNadirAngle"])
            if p.get("offNadirAngle") is not None
            else None,  # ALOS
            "orbit": [str(p["orbit"])],
            "path": p.get("pathNumber"),
            "polarization": p.get("polarization"),
            "pointingAngle": p.get("pointingAngle"),
            "productID": p.get("fileID"),
            "productType": p.get("processingLevel"),
            "productTypeDisplay": p.get("processingTypeDisplay"),
            "sizeMB": p.get("sizeMB"),
            "stackSize": p.get(
                "insarStackSize"
            ),  # Used for datasets with precalculated stacks
            "startTime": p.get("startTime"),
            "stopTime": p.get("stopTime"),
            "thumb": p.get("thumb"),
            "wkt": wrapped,
            "wkt_unwrapped": unwrapped,
            "pgeVersion": p.get("pgeVersion"),
        }

        for key in result.keys():
            if result[key] in ["NA", "NULL"]:
                result[key] = None

        if "temporalBaseline" in p.keys() or "perpendicularBaseline" in p.keys():
            result["temporalBaseline"] = p["temporalBaseline"]
            result["perpendicularBaseline"] = p["perpendicularBaseline"]

        if p.get("processingLevel") == "BURST":  # is a burst product
            result["burst"] = p["burst"]

        if p.get('operaBurstID') is not None or result['productID'].startswith('OPERA'):
            result['opera'] = {
                'operaBurstID': p.get('operaBurstID'),
                'additionalUrls': p.get('additionalUrls'),
            }
            if p.get('validityStartDate'):
                result['opera']['validityStartDate'] = p.get('validityStartDate')

        return result

    def getOutputType(self) -> str:
        return "jsonlite"
