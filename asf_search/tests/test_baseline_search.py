from asf_search.ASFSearchResults import ASFSearchResults
from asf_search.constants import PLATFORM
from asf_search.exceptions import ASFBaselineError
from ..search.search import ASFProduct
from ..search.baseline_search import calc_temporal_baselines, get_stack_params, stack_from_product
import pytest
from .fixtures.baseline_search_fixtures import *

from unittest.mock import patch

class Test_Baseline_Search:
  def test_get_stack_params_alos(self, alos_search_response):
      search_results = ASFSearchResults(alos_search_response)

      idx = 1
      reference = ASFProduct(search_results[idx])
      params = get_stack_params(reference)

      original_properties = alos_search_response[idx]['properties']
      assert(params['processingLevel'] == [original_properties['processingLevel']])
      assert(params['insarStackId'] == original_properties['insarStackId'])
      assert(len(params) == 2)
      

  def test_get_stack_params_sentinel(self, s1_search_response):
      search_results = ASFSearchResults(s1_search_response)

      idx = 1
      reference = ASFProduct(search_results[idx])
      params = get_stack_params(reference)

      original_properties = s1_search_response[idx]['properties']
      
      assert(original_properties['polarization'] in params['polarization'])
      assert(['VV', 'VV+VH'] == params['polarization'])
      assert(len(params) == 7)

  def test_get_stack_params_invalid_insarStackId_raises_error(self, alos_search_response):
      search_results = ASFSearchResults(alos_search_response)

      idx = -1
      invalid_reference = ASFProduct(search_results[idx])
      
      invalid_reference.properties['insarStackId'] = '0'

      with pytest.raises(ASFBaselineError):
        get_stack_params(invalid_reference)
      
  def test_get_stack_params_invalid_platform_raises_error(self, s1_search_response):
      search_results = ASFSearchResults(s1_search_response)

      idx = -1
      invalid_reference = ASFProduct(search_results[idx])
      
      invalid_reference.properties['platform'] = None
      
      with pytest.raises(ASFBaselineError):
        get_stack_params(invalid_reference)
    
  def test_calc_temporal_baselines(self, s1_search_response, s1_baseline_stack):
    reference = ASFProduct(s1_search_response[0])
    
    stack = ASFSearchResults(map(self.toASFProduct, s1_baseline_stack))
    
    calc_temporal_baselines(reference, stack)

    assert(len(stack) == 4)
    for secondary in stack:
      assert(secondary.properties['temporalBaseline'] >= 0)
    # assert stack


  def toASFProduct(self, secondary):
    return ASFProduct(secondary)


  def test_stack_from_product(self, s1_search_response, s1_baseline_stack):
    reference = ASFProduct(s1_search_response[0])

    with patch('asf_search.baseline_search.search') as search_mock:
      search_mock.return_value = ASFSearchResults(map(self.toASFProduct, s1_baseline_stack))    
      
      stack = stack_from_product(reference)
      
      assert(len(stack) == 4)
      for (idx, secondary) in enumerate(stack):
        assert(secondary.properties['temporalBaseline'] >= 0)
        
        if(idx > 0):
          assert(secondary.properties['temporalBaseline'] >= 0)

