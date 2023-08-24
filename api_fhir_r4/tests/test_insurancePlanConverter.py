import json
import os

from api_fhir_r4.converters import InsurancePlanConverter

from fhir.resources.R4B.insuranceplan import InsurancePlan
from api_fhir_r4.tests import InsurancePlanTestMixin
from api_fhir_r4.tests.mixin import ConvertToImisTestMixin, ConvertToFhirTestMixin, ConvertJsonToFhirTestMixin


class InsurancePlanConverterTestCase(InsurancePlanTestMixin,
                                     ConvertToImisTestMixin,
                                     ConvertToFhirTestMixin,
                                     ConvertJsonToFhirTestMixin):
    converter = InsurancePlanConverter
    fhir_resource = InsurancePlan
    json_repr = 'test/test_insurance_plan.json'
