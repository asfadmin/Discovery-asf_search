import datetime
from typing import Optional, Sequence, Tuple, Union
from asf_search import ASF_LOGGER
from asf_search.ASFSession import ASFSession
from asf_search.ASFSearchOptions.config import config
from asf_search.constants import INTERNAL

from .validators import (
    parse_string,
    parse_float,
    parse_wkt,
    parse_date,
    parse_string_list,
    parse_int_list,
    parse_int_or_range_list,
    parse_float_or_range_list,
    parse_cmr_keywords_list,
    parse_session,
)

from pydantic import ValidationError, create_model, field_validator, InstanceOf


# def validate(key, value):
#     if key not in validator_map:
#         error_msg = f"Key '{key}' is not a valid search option."
#         # See if they just missed up case sensitivity:
#         for valid_key in validator_map:
#             if key.lower() == valid_key.lower():
#                 error_msg += f" (Did you mean '{valid_key}'?)"
#                 break
#         ASF_LOGGER.error(error_msg)
#         raise KeyError(error_msg)
#     try:
#         return validator_map[key](value)
#     except ValueError as exc:
#         ASF_LOGGER.exception(
#             f"Failed to parse item in ASFSearchOptions: {key=} {value=} {exc=}"
#         )
#         raise


validators = {
    "int_or_range_list_validator": field_validator("absoluteOrbit", "asfFrame", "frame", "relativeOrbit")(parse_int_or_range_list),
    "string_list_validator": field_validator(
        "beamMode",
        "beamSwath",
        "granule_list",
        "product_list",
        "platform",
        "polarization",
        "processingLevel",
        "groupID",
        "collections",
        "shortName",
        "temporalBaselineDays",
        "operaBurstID",
        "fullBurstID",
        "dataset")(parse_string_list),
    "string_validator": field_validator("campaign",
        "flightDirection",
        "flightLine",
        "lookDirection",
        "insarStackId",
        "instrument",
        "host",
        "provider")(parse_string),
    "float_or_range_list_validator": field_validator("offNadirAngle")(parse_float_or_range_list),
    "float_validator": field_validator(
        "maxDoppler",
        "minDoppler",
        "maxFaradayRotation",
        "minFaradayRotation",)(parse_float),
    "wkt_validator": field_validator("intersectsWith")(parse_wkt),
    "date_validator": field_validator("processingDate", "start", "end")(parse_date),
    "cmr_keywords_list_validator": field_validator("cmr_keywords")(parse_cmr_keywords_list),
    "session_validator": field_validator("session")(parse_session),
}

ASFSearchOptionsModel = create_model(
    "ASFSearchOptionsModel",
    absoluteOrbit = (Optional[Union[int, Tuple[int, int], type(range), Sequence[Union[int, Tuple[int, int], type(range)]]]],  None),
    asfFrame = (Optional[Union[int, Tuple[int, int], type(range), Sequence[Union[int, Tuple[int, int], type(range)]]]],  None),
    beamMode = (Optional[Union[str, Sequence[str]]],  None),
    beamSwath = (Optional[Union[str, Sequence[str]]],  None),
    campaign = (Optional[Union[str, Sequence[str]]],  None),
    maxDoppler = (Optional[float],  None),
    minDoppler = (Optional[float],  None),
    end = (Optional[Union[datetime.datetime, str]],  None),
    maxFaradayRotation = (Optional[float],  None),
    minFaradayRotation = (Optional[float],  None),
    flightDirection = (Optional[str],  None),
    flightLine = (Optional[str],  None),
    frame = (Optional[Union[int, Tuple[int, int], type(range), Sequence[Union[int, Tuple[int, int], type(range)]]]],  None),
    granule_list = (Optional[Union[str, Sequence[str]]],  None),
    groupID = (Optional[Union[str, Sequence[str]]],  None),
    insarStackId = (Optional[str],  None),
    instrument = (Optional[Union[str, Sequence[str]]],  None),
    intersectsWith = (Optional[str],  None),
    lookDirection = (Optional[Union[str, Sequence[str]]],  None),
    offNadirAngle = (Optional[Union[float, Tuple[float, float], Sequence[Union[float, Tuple[float, float]]]]],  None),
    platform = (Optional[Union[str, Sequence[str]]],  None),
    polarization = (Optional[Union[str, Sequence[str]]],  None),
    processingDate = (Optional[Union[datetime.datetime, str]],  None),
    processingLevel = (Optional[Union[str, Sequence[str]]],  None),
    product_list = (Optional[Union[str, Sequence[str]]],  None),
    relativeOrbit = (Optional[Union[int, Tuple[int, int], type(range), Sequence[Union[int, Tuple[int, int], type(range)]]]],  None),
    season = (Optional[Tuple[int, int]],  None),
    start = (Optional[Union[datetime.datetime, str]],  None),
    absoluteBurstID = (Optional[Union[int, Sequence[int]]],  None),
    relativeBurstID = (Optional[Union[int, Sequence[int]]],  None),
    fullBurstID = (Optional[Union[str, Sequence[str]]],  None),
    collections = (Optional[Union[str, Sequence[str]]],  None),
    temporalBaselineDays = (Optional[Union[str, Sequence[str]]],  None),
    operaBurstID = (Optional[Union[str, Sequence[str]]],  None),
    dataset = (Optional[Union[str, Sequence[str]]],  None),
    shortName = (Optional[Union[str, Sequence[str]]],  None),
    cmr_keywords = (Optional[Union[Tuple[str, str], Sequence[Tuple[str, str]]]],  None),
    maxResults = (Optional[int],  None),
    session = (Optional[InstanceOf[ASFSession]], config['session']),
    host = (Optional[str], config['host']),
    provider = (Optional[str], config['provider']),
    collectionAlias = (Optional[bool], config['collectionAlias']),
    __validators__= validators,
    __config__= {
        'validate_assignment': True
    }
    
)


# {
#     "int": ["maxResults"],
#     "parse_int_or_type(range)_list": ["absoluteOrbit", "asfFrame", "frame", "relativeOrbit"],
#     "parse_string_list": [
#         "beamMode",
#         "beamSwath",
#         "granule_list",
#         "product_list",
#         "platform",
#         "polarization",
#         "processingLevel",
#         "groupID",
#         "collections",
#         "shortName",
#         "temporalBaselineDays",
#         "operaBurstID",
#         "fullBurstID",
#         "dataset",
#     ],
#     "parse_string": [
#         "campaign",
#         "flightDirection",
#         "flightLine",
#         "lookDirection",
#         "insarStackId",
#         "instrument",
#         "host",
#         "provider",
#     ],
#     "parse_float": [
#         "maxDoppler",
#         "minDoppler",
#         "maxFaradayRotation",
#         "minFaradayRotation",
#     ],
#     "parse_wkt": ["intersectsWith"],
#     "parse_float_or_type(range)_list": ["offNadirAngle"],
#     "parse_date": ["processingDate", "start", "end"],
#     "parse_int_list": ["season", "absoluteBurstID", "relativeBurstID"],
#     "parse_cmr_keywords_list": ["cmr_keywords"],
#     "parse_session": ["session"],
#     "bool": ["collectionAlias"],
# }
# validator_map = {
#     # Search parameters       Parser
#     "maxResults": int,
#     "absoluteOrbit": parse_int_or_type(range)_list,
#     "asfFrame": parse_int_or_type(range)_list,
#     "beamMode": parse_string_list,
#     "beamSwath": parse_string_list,
#     "campaign": parse_string,
#     "maxDoppler": parse_float,
#     "minDoppler": parse_float,
#     "maxFaradayRotation": parse_float,
#     "minFaradayRotation": parse_float,
#     "flightDirection": parse_string,
#     "flightLine": parse_string,
#     "frame": parse_int_or_type(range)_list,
#     "granule_list": parse_string_list,
#     "product_list": parse_string_list,
#     "intersectsWith": parse_wkt,
#     "lookDirection": parse_string,
#     "offNadirAngle": parse_float_or_type(range)_list,
#     "platform": parse_string_list,
#     "polarization": parse_string_list,
#     "processingLevel": parse_string_list,
#     "relativeOrbit": parse_int_or_type(range)_list,
#     "processingDate": parse_date,
#     "start": parse_date,
#     "end": parse_date,
#     "season": parse_int_list,
#     "groupID": parse_string_list,
#     "insarStackId": parse_string,
#     "instrument": parse_string,
#     "collections": parse_string_list,
#     "shortName": parse_string_list,
#     "temporalBaselineDays": parse_string_list,
#     "operaBurstID": parse_string_list,
#     "absoluteBurstID": parse_int_list,
#     "relativeBurstID": parse_int_list,
#     "fullBurstID": parse_string_list,
#     "dataset": parse_string_list,
#     "cmr_keywords": parse_cmr_keywords_list,
#     # Config parameters       Parser
#     "session": parse_session,
#     "host": parse_string,
#     "provider": parse_string,
#     "collectionAlias": bool,
# }
