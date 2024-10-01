import logging
from collections import defaultdict, OrderedDict
from datetime import datetime as py_datetime
from django.db.models import Q
from django.http import Http404
from itertools import chain
from rest_framework.request import Request
from rest_framework.response import Response

from api_fhir_r4.defaultConfig import DEFAULT_CFG
from api_fhir_r4.mixins import MultiIdentifierRetrieveManySerializersMixin, MultiIdentifierRetrieverMixin
from api_fhir_r4.model_retrievers import (
    CodeIdentifierModelRetriever,
    DatabaseIdentifierModelRetriever,
    UUIDIdentifierModelRetriever
)
from api_fhir_r4.multiserializer import modelViewset
from api_fhir_r4.permissions import (
    FHIRApiOrganizationPermissions,
    FHIRApiHealthServicePermissions,
    FHIRApiInsuranceOrganizationPermissions
)
from api_fhir_r4.views.fhir.base import BaseMultiserializerFHIRView
from api_fhir_r4.serializers import (
    PolicyHolderOrganisationSerializer,
    HealthFacilityOrganisationSerializer,
    InsuranceOrganizationSerializer
)
from api_fhir_r4.views.filters import (
    ValidityFromRequestParameterFilter,
    DateUpdatedRequestParameterFilter
)
from location.models import HealthFacility
from core.models import ModuleConfiguration
from policyholder.models import PolicyHolder

logger = logging.getLogger(__name__)


class OrganisationViewSet(BaseMultiserializerFHIRView,
                          modelViewset.MultiSerializerModelViewSet,
                          MultiIdentifierRetrieveManySerializersMixin, MultiIdentifierRetrieverMixin):
    retrievers = [UUIDIdentifierModelRetriever, DatabaseIdentifierModelRetriever, CodeIdentifierModelRetriever]

    lookup_field = 'identifier'

    @property
    def serializers(self):
        return {
            HealthFacilityOrganisationSerializer:
                (self._hf_queryset(), self._hf_serializer_validator, (FHIRApiHealthServicePermissions,)),
            PolicyHolderOrganisationSerializer:
                (self._ph_queryset(), self._ph_serializer_validator, (FHIRApiOrganizationPermissions,)),
            InsuranceOrganizationSerializer:
                (self._io_queryset(), self._io_serializer_validator, (FHIRApiInsuranceOrganizationPermissions,)),
        }

    @classmethod
    def _hf_serializer_validator(cls, context):
        return cls._base_request_validator_dispatcher(
            request=context['request'],
            get_check=lambda x: cls._get_type_from_query(x) in ('prov', None),
            post_check=lambda x: cls._get_type_from_body(x) == 'prov',
            put_check=lambda x: cls._get_type_from_body(x) in ('prov', None),
        )

    @classmethod
    def _ph_serializer_validator(cls, context):
        return cls._base_request_validator_dispatcher(
            request=context['request'],
            get_check=lambda x: cls._get_type_from_query(x) in ('bus', None),
            post_check=lambda x: cls._get_type_from_body(x) == 'bus',
            put_check=lambda x: cls._get_type_from_body(x) in ('bus', None),
        )

    @classmethod
    def _io_serializer_validator(cls, context):
        return cls._base_request_validator_dispatcher(
            request=context['request'],
            get_check=lambda x: cls._get_type_from_query(x) in ('ins', None),
            post_check=lambda x: cls._get_type_from_body(x) == 'ins',
            put_check=lambda x: cls._get_type_from_body(x) in ('ins', None),
        )

    @classmethod
    def _base_request_validator_dispatcher(cls, request: Request, get_check, post_check, put_check):
        if request.method == 'GET':
            return get_check(request)
        elif request.method == 'POST':
            return post_check(request)
        elif request.method == 'PUT':
            return put_check(request)
        return True

    def list(self, request, *args, **kwargs):
        resource_type = request.GET.get("resourceType")
        type_ = request.GET.get("type")
        identifier = request.GET.get("code")
        if identifier:
            return self.retrieve(request, *args, **{**kwargs, 'identifier': identifier})

        self._validate_list_model_request()
        filtered_querysets = {}  # {serialzer: qs}

        for serializer, (qs, _, _) in self.get_eligible_serializers_iterator():
            next_serializer_data = self.filter_queryset(qs)
            model = next_serializer_data.model
            filtered_querysets[model, serializer] = next_serializer_data

        # if insurance organisation queryset is empty - take the default one
        if resource_type is None or resource_type == 'ins':
            if (ModuleConfiguration, InsuranceOrganizationSerializer) in filtered_querysets:
                if len(filtered_querysets[ModuleConfiguration, InsuranceOrganizationSerializer]) == 0:
                    filtered_querysets[ModuleConfiguration, InsuranceOrganizationSerializer] = \
                        [DEFAULT_CFG['R4_fhir_insurance_organisation_config']]
                else:
                    # save in 'filtered_queryset' values from module db config to have good value in 'total_count'
                    filtered_querysets[ModuleConfiguration, InsuranceOrganizationSerializer] = \
                        self._get_insurance_organisations_as_list()

        page = self.paginate_queryset(list(chain(*filtered_querysets.values())))
        data = self.__dispatch_page_data(page)
        serialized_data = self._serialize_dispatched_data(data, dict(filtered_querysets.keys()), user=request.user)
        data = self.get_paginated_response(serialized_data)
        return data

    def __dispatch_page_data(self, page):
        x = defaultdict(list)
        for r in page:
            x[type(r)].append(r)
        return x

    def retrieve(self, request, *args, **kwargs):
        self._validate_retrieve_model_request()
        retrieved = []
        errors = []
        for serializer, (qs, _, _) in self.get_eligible_serializers_iterator():
            if qs.model is not ModuleConfiguration:
                try:
                    ref_type, instance = self._get_object_with_first_valid_retriever(qs, kwargs['identifier'])
                    if instance:
                        serializer = serializer(instance, reference_type=ref_type, user=request.user)
                        if serializer.data:
                            retrieved.append(serializer.data)
                except Exception as e:
                    # we will try with another retriever
                    errors.append(str(e))
            else:
                if qs.count() > 0:
                    data = self._get_insurance_organisation(kwargs.get('identifier', None))
                else:
                    data = self._get_insurance_organisation_default(kwargs.get('identifier', None))
                if data:
                    retrieved.append(data)

        if len(retrieved) > 1:
            raise ValueError("Ambiguous retrieve result, object found for multiple serializers.")
        elif len(retrieved) == 0:
            if len(errors) > 0:
                raise Http404(f"Resource for identifier {kwargs['identifier']} cannot be reloved:{','.join(errors)}")
            else:
                raise Http404(f"Resource for identifier {kwargs['identifier']} not found")

        return Response(retrieved[0])

    def _get_insurance_organisations_as_list(self):
        data = []
        module_config = self._io_queryset()[0]._cfg
        if 'insurer_organisation' in module_config:
            insurer_organisations = module_config['insurer_organisation']
            for ins in insurer_organisations:
                data.append(ins)
        return data

    def _get_insurance_organisations(self):
        """method to get insurance organisation from module fhir config"""
        data = []
        serializer = InsuranceOrganizationSerializer()
        module_config = self._io_queryset()[0]._cfg
        if 'insurer_organisation' in module_config:
            insurer_organisations = module_config['insurer_organisation']
            for ins in insurer_organisations:
                data.append(serializer.to_representation(obj=ins))
        return data

    def _get_insurance_organisation(self, identifier):
        """method to get chosen insurance organisation from module fhir config"""
        insurer_organisations = self._get_insurance_organisations()
        if len(insurer_organisations) > 0:
            for ins in insurer_organisations:
                if identifier == f"{ins['id']}":
                    return ins

    def _get_insurance_organisation_default(self, identifier, user=None):
        """method to get chosen insurance organisation from default config if no config in db"""
        serializer = InsuranceOrganizationSerializer(user=user)
        default_insurance_organisation = DEFAULT_CFG['R4_fhir_insurance_organisation_config']
        if identifier == f"{default_insurance_organisation['id']}":
            return serializer.to_representation(obj=default_insurance_organisation)

    def get_queryset(self):
        return HealthFacility.objects

    def _hf_queryset(self):
        queryset = HealthFacility.objects.filter(validity_to__isnull=True).order_by('validity_from')
        return ValidityFromRequestParameterFilter(self.request).filter_queryset(queryset)

    def _ph_queryset(self):
        queryset = PolicyHolder.objects.filter(is_deleted=False).order_by('date_created')
        return DateUpdatedRequestParameterFilter(self.request).filter_queryset(queryset)

    def _io_queryset(self):
        now = py_datetime.now()  # can't use core config here...
        queryset = ModuleConfiguration.objects.filter(
            Q(is_disabled_until=None) | Q(is_disabled_until__lt=now),
            layer='be',
            module='api_fhir_r4')
        return DateUpdatedRequestParameterFilter(self.request).filter_queryset(queryset)

    @classmethod
    def _get_type_from_body(cls, request):
        try:
            # See: http://hl7.org/fhir/R4/organization.html
            return request.data['type'][0]['coding'][0]['code'].lower()
        except KeyError:
            return None

    @classmethod
    def _get_type_from_query(cls, request):
        try:
            return request.GET['type'].lower()
        except KeyError:
            return None

    def _serialize_dispatched_data(self, data, serializer_models, user=None):
        # override this method to support InsuranceOrganisation serializer
        #  solution - model taken from ModuleConfiguration model
        serialized = []
        for model, model_data in data.items():
            serializer_cls = serializer_models.get(model, None)
            if not serializer_cls:
                if all(isinstance(md, OrderedDict) for md in model_data):
                    serialized.extend(self._get_insurance_organisations())
                else:
                    # check if we have insurance organisation default config
                    data_default = self.__check_default_config_insurance_organisation(model_data, user=user)
                    if len(data_default) > 0:
                        serialized.extend(data_default)
                    else:
                        logger.error(f"Found data of type {model_data} but it couldn't be matched with "
                                     f"any of available serializers {serializer_models}")
                    continue
            else:
                serializer = serializer_cls(tuple(model_data), many=True, user=user)
                serialized.extend(serializer.data)

        return serialized

    def __check_default_config_insurance_organisation(self, model_data, user=None):
        for md in model_data:
            if md.get('resource_type') == 'insurance_organisation':
                identifier = DEFAULT_CFG['R4_fhir_insurance_organisation_config']['id']
                return [self._get_insurance_organisation_default(identifier=identifier, user=user)]
