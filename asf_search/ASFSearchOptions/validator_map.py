import datetime
from typing import Any, ClassVar, List, Optional, Sequence, Tuple, Union
from typing_extensions import Annotated
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
    parse_float_list
)

from pydantic import BaseModel, ConfigDict, Field, InstanceOf, PlainValidator, ValidationError, ValidationInfo, field_validator, model_validator

int_range_or_list = Annotated[
    Optional[Union[int, Tuple[int, int], Sequence[Union[int, Tuple[int, int]]]]],
    PlainValidator(parse_int_or_range_list), 
    # BeforeValidator(string_to_num_or_range_list)
    ]

float_range_or_list = Annotated[
    Optional[Union[int, Tuple[float, float], Sequence[Union[float, Tuple[float, float]]]]],
    PlainValidator(parse_float_or_range_list), 
    # BeforeValidator(string_to_num_or_range_list)
    ]

string_list = Annotated[
    Optional[Union[str, Sequence[str]]], 
    PlainValidator(parse_string_list),
    # BeforeValidator(string_to_list)
    ]

int_list = Annotated[
    Optional[Union[int, Sequence[int]]],
    PlainValidator(parse_int_list),
    # BeforeValidator(string_to_list)
]

float_list = Annotated[
    Optional[Union[float, Sequence[float]]],
    PlainValidator(parse_float_list),
    # BeforeValidator(string_to_list)
]

date_type = Annotated[Optional[Union[datetime.datetime, str]], PlainValidator(parse_date)]

cmr_keyword_type = Annotated[Optional[Union[Tuple[str, str], Sequence[Tuple[str, str]]]], PlainValidator(parse_cmr_keywords_list)]
class SearchOptionsModel(BaseModel):
    absoluteOrbit: int_range_or_list = None
    asfFrame: int_range_or_list = None
    beamMode: string_list = None
    beamSwath: string_list = None
    campaign: string_list = None # Field(validation_alias=AliasPath('collectionname', None))
    # circle:  cirle_type = None
    # linestring: linestring_type = None
    maxDoppler: Optional[float] = None
    minDoppler: Optional[float] = None
    end: date_type = None
    maxFaradayRotation: Optional[float] = None
    minFaradayRotation: Optional[float] = None
    flightDirection: Optional[str] = None
    flightLine: Optional[str] = None
    frame: int_range_or_list = None
    granule_list: string_list = None
    groupID: string_list = None
    insarStackId: Optional[str] = None
    instrument: string_list = None
    intersectsWith: Optional[str] = None
    lookDirection: string_list = None
    offNadirAngle: float_range_or_list = None
    platform: string_list = None
    polarization: string_list = None
    processingDate: date_type = None
    processingLevel: string_list = None
    product_list: string_list = None
    relativeOrbit: int_range_or_list = None
    season: int_list = None
    start: date_type = None
    absoluteBurstID: int_list = None
    relativeBurstID: int_list = None
    fullBurstID: string_list = None
    collections: string_list = None
    temporalBaselineDays: string_list = None
    operaBurstID: string_list = None
    dataset: string_list = None
    shortName: string_list = None
    cmr_keywords: cmr_keyword_type = None

    maxResults: Optional[int] = Field(default=None, gt=0)

    # config
    session: Annotated[Optional[InstanceOf[ASFSession]], PlainValidator(parse_session)] = config['session']
    host: Optional[str] = config['host']
    provider: Optional[str] = config['provider']
    collectionAlias: Optional[bool] = config['collectionAlias']
    

    output: str = 'metalink'
    maturity: Optional[str] = None
    cmr_token: Optional[str] = None

    excluded_fields: ClassVar[List[str]] = ['cmr_token', 'maturity', 'output']

    model_config = ConfigDict(extra='forbid', validate_assignment=True)
    
    def _get_search_options_dict(self) -> dict:
        return self.model_dump(exclude_none=True, exclude_unset=True, exclude=self.excluded_fields)
    
    # @model_validator(mode='before')
    # @classmethod
    # def validate_field(cls, data):
    #     key = data.field_name
    #     print(f"KEY {key}")
    #     if key not in SearchOptionsModel.model_fields:
    #         error_msg = f"Key '{key}' is not a valid search option."
    #         # See if they just missed up case sensitivity:
    #         for valid_key in SearchOptionsModel.model_fields:
    #             if key.lower() == valid_key.lower():
    #                 error_msg += f" (Did you mean '{valid_key}'?)"
    #                 break
    #         ASF_LOGGER.error(error_msg)
    #         raise ValidationError(error_msg)
        
    #     return v
        
        # try:
        #     return handler(v)
        # except ValueError as exc:
        #     ASF_LOGGER.exception(
        #         f"Failed to parse item in ASFSearchOptions: {key=} {v=} {exc=}"
        #     )
        #     raise
