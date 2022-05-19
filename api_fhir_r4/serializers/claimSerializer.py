from claim.services import ClaimSubmitService, ClaimSubmit, ClaimConfig
from claim.gql_mutations import create_attachments
from claim.models import Claim, ClaimAdmin, ClaimItem, ClaimService
from typing import List, Union

from api_fhir_r4.containedResources.claimContainedResources import ClaimContainedResources
from api_fhir_r4.containedResources.serializerMixin import ContainedContentSerializerMixin
from api_fhir_r4.models import ClaimV2 as FHIRClaim
from django.http import HttpResponseForbidden
from django.http.response import HttpResponseBase
from django.shortcuts import get_object_or_404

from api_fhir_r4.configurations import R4ClaimConfig, GeneralConfiguration
from api_fhir_r4.converters import ClaimResponseConverter, OperationOutcomeConverter, ReferenceConverterMixin as r
from api_fhir_r4.converters.claimConverter import ClaimConverter
from fhir.resources.fhirabstractmodel import FHIRAbstractModel
from api_fhir_r4.serializers import BaseFHIRSerializer


class ClaimSerializer(ContainedContentSerializerMixin, BaseFHIRSerializer):

    fhirConverter = ClaimConverter()

    contained_resources = ClaimContainedResources

    def fhir_object_reference_fields(self, fhir_obj: FHIRClaim) -> List[FHIRAbstractModel]:
        return [
            fhir_obj.patient,
            fhir_obj.provider,
            fhir_obj.enterer,
            *[item.extension[0].valueReference for item in fhir_obj.item]
        ]

    def create(self, validated_data):
        from_contained = self._create_or_update_contained(self.initial_data)
        claim = self._create_claim_from_validated_data(validated_data, from_contained)
        return self.create_claim_response(claim.code)

    def create_claim_response(self, claim_code):
        claim = get_object_or_404(Claim, code=claim_code, validity_to=None)
        return ClaimResponseConverter.to_fhir_obj(claim)

    def create_claim_attachments(self, claim_code, attachments):
        claim = get_object_or_404(Claim, code=claim_code, validity_to=None)
        create_attachments(claim.id, attachments)

    def to_representation(self, obj):
        if isinstance(obj, HttpResponseBase):
            return OperationOutcomeConverter.to_fhir_obj(obj).dict()
        elif isinstance(obj, FHIRAbstractModel):
            return obj.dict()

        fhir_obj = self.fhirConverter.to_fhir_obj(obj, self._reference_type)
        self.remove_attachment_data(fhir_obj)
        
        if self.context.get('contained', None):
            self._add_contained_references(fhir_obj)

        fhir_dict = fhir_obj.dict()
        if self.context.get('contained', False):
            fhir_dict['contained'] = self._create_contained_obj_dict(obj)
        return fhir_dict

    def remove_attachment_data(self, fhir_obj):
        if hasattr(self.parent, 'many') and self.parent.many is True:
            attachments = self.__get_attachments(fhir_obj)
            for next_attachment in attachments:
                next_attachment.data = None

    @property
    def reference_type(self):
        return super().reference_type

    @reference_type.setter
    def reference_type(self, reference_type: Union[r.UUID_REFERENCE_TYPE,
                                                   r.CODE_REFERENCE_TYPE,
                                                   r.DB_ID_REFERENCE_TYPE]):
        if reference_type != self._reference_type:
            self._reference_type = reference_type
            self.__set_contained_resource_reference_types(reference_type)

    def __get_attachments(self, fhir_obj):
        attachment_category = R4ClaimConfig.get_fhir_claim_attachment_code()
        return [a.valueAttachment for a in fhir_obj.supportingInfo if a.category.text == attachment_category]

    def __set_contained_resource_reference_types(self, reference_type):
        self._contained_definitions.update_reference_type(reference_type)

    def __claim_provisions_to_dict(self, list_of_provisions, contained_items):
        # Claim Entering service is expecting to receive items and services in form of
        # dict and then uses process_items_relations or process_services_relations to create actual items.
        out = []
        for x in list_of_provisions:
            dict_ = x.__dict__
            dict_.pop('_state', None)
            if isinstance(x, ClaimItem):
                dict_['item_id'] = \
                    self.__get_contained_medical_provision(contained_items, dict_) or dict_['item_id']
            elif isinstance(x, ClaimService):
                dict_['service_id'] = \
                    self.__get_contained_medical_provision(contained_items, dict_) or dict_['service_id']
            else:
                raise AttributeError(F"Medical provision {x} is not ClaimItem nor ClaimService")

            dict_.pop('code')
            out.append(dict_)
        return out

    def __get_contained_or_default_hf_id(self, contained_dict, validated_data):
        contained_value = self.__id_from_contained(
            contained_dict['health_facility__Organization'],
            lambda x: x.code == validated_data['health_facility_code'])
        return contained_value or validated_data['health_facility_id']

    def __get_contained_or_default_insuree(self, contained_dict, validated_data):
        contained_value = self.__id_from_contained(
            contained_dict['insuree__Patient'],
            lambda x: x.chf_id == validated_data['insuree_chf_code'])
        return contained_value or validated_data['insuree_id']

    def __get_contained_or_default_claim_admin(self, contained_dict, validated_data):
        contained_value = self.__id_from_contained(
            contained_dict['admin__Practitioner'],
            lambda x: x.code == validated_data['claim_admin_code'])
        return contained_value or validated_data['admin_id']

    def __get_contained_medical_provision(self, contained_items: list, item):
        contained_value = self.__id_from_contained(contained_items, lambda x: x.code == item['code'])
        return contained_value

    def __id_from_contained(self, contained_collection, lookup_func):
        matching = [x.id for x in contained_collection if lookup_func(x)]
        return matching[0] if len(matching) != 0 else None

    def _create_claim_from_validated_data(self, validated_data, contained):
        truncated_data = self._claim_input_from_validated_claim_data(validated_data, contained)
        user = self.context.get("request").user
        if not user or not user.has_perms(
                ClaimConfig.gql_mutation_create_claims_perms
                + ClaimConfig.gql_mutation_submit_claims_perms
        ):
            return HttpResponseForbidden()

        rule_engine_validation = GeneralConfiguration.get_claim_rule_engine_validation()
        claim = ClaimSubmitService(user) \
            .enter_and_submit(truncated_data, rule_engine_validation=rule_engine_validation)

        attachments = validated_data.get('claim_attachments', [])
        self.create_claim_attachments(claim.code, attachments)
        return claim

    def _claim_input_from_validated_claim_data(self, validated_data, contained):
        essential_claim_fields = [
            'date_claimed', 'date_from', 'date_to',
            'icd_id', 'icd_1_id', 'icd_2_id', 'icd_3_id', 'icd_4_id',
            'code',
            'claimed',
            'explanation',
            'adjustment',
            'category',
            'visit_type',
            'guarantee_id',

            'insuree_id',
            'health_facility_id',
            'admin_id',

            'items',
            'services',

            'json_ext'
        ]
        truncated_data = {k: v for k, v in validated_data.items() if k in essential_claim_fields}
        truncated_data.pop('_state', None)

        # Items and services passed in converter through additional attributes
        truncated_data['items'] = self.__claim_provisions_to_dict(
            validated_data['submit_items'],
            contained['items__Medication'])

        truncated_data['services'] = self.__claim_provisions_to_dict(
            validated_data['submit_services'],
            contained['services__ActivityDefinition'])

        # If those resources are created through contained id is not available until _create_or_update_contained is
        # called. This ensures references are ok. Codes are assigned in converter as additional variables.
        # .get() is used as those values are mandatory in claim and have to be unique.
        truncated_data['health_facility_id'] = self.__get_contained_or_default_hf_id(contained, validated_data)
        truncated_data['insuree_id'] = self.__get_contained_or_default_insuree(contained, validated_data)
        truncated_data['admin_id'] = self.__get_contained_or_default_claim_admin(contained, validated_data)
        return truncated_data
