from api_fhir_r4.converters import OperationOutcomeConverter
from api_fhir_r4.permissions import FHIRApiClaimPermissions, FHIRApiCoverageEligibilityRequestPermissions, \
    FHIRApiCoverageRequestPermissions, FHIRApiCommunicationRequestPermissions, FHIRApiPractitionerPermissions, \
    FHIRApiHFPermissions, FHIRApiInsureePermissions, FHIRApiMedicationPermissions, FHIRApiConditionPermissions, \
    FHIRApiActivityDefinitionPermissions, FHIRApiHealthServicePermissions, FHIRApiGroupPermissions, \
    FHIRApiOrganizationPermissions
from claim.models import ClaimAdmin, Claim, Feedback, ClaimItem, ClaimService
from core.models import User
from django.db.models import OuterRef, Exists
from insuree.models import Insuree, InsureePolicy,Family
from policyholder.models import PolicyHolder
from location.models import HealthFacility, Location
from policy.models import Policy
from medical.models import Item, Diagnosis, Service
from rest_framework import exceptions, viewsets, mixins, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.decorators import parser_classes,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
import os
from api_fhir_r4.paginations import FhirBundleResultsSetPagination
from api_fhir_r4.permissions import FHIRApiPermissions
from api_fhir_r4.configurations import R4CoverageEligibilityConfiguration as Config, GeneralConfiguration
from api_fhir_r4.serializers import PatientSerializer, LocationSerializer, LocationSiteSerializer, PractitionerRoleSerializer, \
    PractitionerSerializer, ClaimSerializer, CoverageEligibilityRequestSerializer, \
    PolicyCoverageEligibilityRequestSerializer, ClaimResponseSerializer, CommunicationRequestSerializer, \
    MedicationSerializer, ConditionSerializer, ActivityDefinitionSerializer, HealthcareServiceSerializer, ContractSerializer, GroupSerializer,\
    OrganisationSerializer
from api_fhir_r4.serializers.coverageSerializer import CoverageSerializer

from django.db.models import Q, Prefetch
from graphql_jwt.utils import jwt_payload
from core.jwt import *
from django.db.models import Prefetch
from rest_framework.decorators import api_view
import datetime
from rest_framework.parsers import JSONParser


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class LoginView(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        data = request.data
        # check if we have both required data in request payload
        if 'username' in data and 'password' in data:
            username = data['username']
            password = data['password']
            users = User.objects.filter(username=username)
            # check if user with such username exists
            if len(list(users)) == 1:
                # validate provided password from payload
                user = users.first()
                if user.check_password(password):
                    # set the user to context
                    request.user = user
                    # take the payload base on user data - using same mechanism as
                    # in graphql_jwt with generating payload.
                    payload = jwt_payload(user=user)
                    # encode token based on payload
                    token = jwt_encode_user_key(payload=payload, context=request)
                    if token:
                        # return ok
                        response = {
                            "token": token,
                            "exp": payload['exp'],
                        }
                        return Response(data=response, status=200)
            # return unauthorized
            return Response(status=401)
        else:
            # return bad request
            return Response(status=400)


class BaseFHIRView(APIView):
    pagination_class = FhirBundleResultsSetPagination
    permission_classes = (FHIRApiPermissions,)
    authentication_classes = [CsrfExemptSessionAuthentication] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES


class InsureeViewSet(BaseFHIRView, viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = PatientSerializer
    permission_classes = (FHIRApiInsureePermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().select_related('gender').select_related('photo').select_related('family__location')
        refDate = request.GET.get('refDate')
        claim_date = request.GET.get('claimDateFrom')
        identifier = request.GET.get("identifier")
        if identifier:
            queryset = queryset.filter(chf_id=identifier)
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from')
            if refDate != None:
                # isValidDate = True
                try :
                    datevar = datetime.datetime.strptime(refDate, "%Y-%m-%d").date()
                except ValueError :
                    pass
                    # isValidDate = False
                #datevar = refDate
                queryset = queryset.filter(validity_from__gte=datevar)
            if claim_date is not None:
                #year,month,day = refDate.split('-')
                try:
                    claim_parse_dated = datetime.datetime.strptime(claim_date, "%Y-%m-%d").date()
                    #datetime.datetime(int(year), int(month), int(day))
                except ValueError:
                    result = OperationOutcomeConverter.build_for_400_bad_request("claimDateFrom should be in dd-mm-yyyy format")
                    return Response(result.dict(), status.HTTP_400_BAD_REQUEST)
                has_claim_in_range = Claim.objects\
                    .filter(date_claimed__gte=claim_parse_dated)\
                    .filter(insuree_id=OuterRef("id"))\
                    .values("id")
                queryset = queryset.annotate(has_claim_in_range=Exists(has_claim_in_range)).filter(has_claim_in_range=True)

        serializer = PatientSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        return Insuree.get_queryset(None, self.request.user)


class GroupViewSet(BaseFHIRView, viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = GroupSerializer
    permission_classes = (FHIRApiGroupPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("identifier") 
        if identifier:
            queryset = queryset.filter(head_insuree_id__chf_id=identifier)
        else:
            queryset = queryset.filter(validity_to__isnull=True)
        serializer = GroupSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        return Family.objects.all().order_by('validity_from')


class OrganisationViewSet(BaseFHIRView, viewsets.ModelViewSet):
    lookup_field = 'id'
    serializer_class = OrganisationSerializer
    permission_classes = (FHIRApiOrganizationPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("code")       
        if identifier:
            queryset = queryset.filter(code=identifier)
        else:
            queryset = queryset.filter().order_by('date_created')
        serializer = OrganisationSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        return PolicyHolder.objects.filter(is_deleted=False).order_by('date_created')


class LocationViewSet(BaseFHIRView, viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = LocationSerializer
    permission_classes = (FHIRApiHFPermissions,)

    def list(self, request, *args, **kwargs):
        identifier = request.GET.get("identifier")
        physicalType = request.GET.get('physicalType')
        queryset = self.get_queryset(physicalType)
        if identifier:
            queryset = queryset.filter(code=identifier)
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from')
        if (physicalType and physicalType == 'si'):
            self.serializer_class=LocationSiteSerializer
            serializer = LocationSiteSerializer(self.paginate_queryset(queryset), many=True)
        else:
            serializer = LocationSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def retrieve(self, *args, **kwargs):
        physicalType = self.request.GET.get('physicalType')
        if ( physicalType and physicalType == 'si'):
            self.serializer_class=LocationSiteSerializer
            self.queryset = self.get_queryset('si')
        response = viewsets.ModelViewSet.retrieve(self, *args, **kwargs)
        return response

    def get_queryset(self, physicalType = 'area'):
        if physicalType == 'si':
            hf_queryset = HealthFacility.get_queryset(None, self.request.user)
            return hf_queryset.select_related('location').select_related('sub_level').select_related('legal_form')
        else:
            return Location.get_queryset(None, self.request.user)


class PractitionerRoleViewSet(BaseFHIRView, viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = PractitionerRoleSerializer
    permission_classes = (FHIRApiPractitionerPermissions,)

    def list(self, request, *args, **kwargs):
        identifier = request.GET.get("identifier")
        queryset = self.get_queryset()
        if identifier:
            queryset = queryset.filter(code=identifier)
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from')

        serializer = PractitionerRoleSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def perform_destroy(self, instance):
        instance.health_facility_id = None
        instance.save()

    def get_queryset(self):
        return ClaimAdmin.get_queryset(None, self.request.user)


class PractitionerViewSet(BaseFHIRView, viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = PractitionerSerializer
    permission_classes = (FHIRApiPractitionerPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        identifier = request.GET.get("identifier")
        if identifier:
            queryset = queryset.filter(code=identifier)
        serializer = PractitionerSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        return ClaimAdmin.get_queryset(None, self.request.user)


class ClaimViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin,
                   mixins.CreateModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    serializer_class = ClaimSerializer
    permission_classes = (FHIRApiClaimPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().select_related('insuree').select_related('health_facility').select_related('icd')\
            .select_related('icd_1').select_related('icd_2').select_related('icd_3').select_related('icd_4')\
            .prefetch_related(Prefetch('items', queryset=ClaimItem.objects.filter(validity_to__isnull=True)))\
            .prefetch_related(Prefetch('services', queryset=ClaimService.objects.filter(validity_to__isnull=True)))\
            .prefetch_related(Prefetch('insuree__insuree_policies', queryset=InsureePolicy.objects.filter(validity_to__isnull=True).select_related("policy"))) #.filter(start_date__lte=date_from , expiry_date__gte=date_from)
        refDate = request.GET.get('refDate')
        identifier = request.GET.get("identifier")
        patient = request.GET.get("patient")
        contained = bool(request.GET.get("contained"))

        if identifier is not None:
            queryset = queryset.filter(Q(code=identifier) | Q(id=identifier) | Q(uuid=identifier))
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from')
            if refDate is not None:
                year,month,day = refDate.split('-')
                # isValidDate = True
                try :
                    datetime.datetime(int(year),int(
                        
                        month),int(day))
                except ValueError :
                    pass
                    #isValidDate = False
                datevar = refDate
                queryset = queryset.filter(validity_from__gte=datevar)
            if patient is not None:
                for_patient = Insuree.objects\
                    .filter(indentifier = patient)\
                    .values("id")
                queryset = queryset.filter(chf_id in indentifier.id)
        serializer = ClaimSerializer(self.paginate_queryset(queryset), many=True, context={'contained': contained})
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        contained = bool(request.GET.get("contained"))
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'contained': contained})
        return Response(serializer.data)

    def get_queryset(self):
        return Claim.get_queryset(None, self.request.user)


class ClaimResponseViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet,
                           mixins.UpdateModelMixin):
    lookup_field = 'uuid'
    serializer_class = ClaimResponseSerializer
    permission_classes = (FHIRApiClaimPermissions,)

    def get_queryset(self):
        return Claim.get_queryset(None, self.request.user)


class CommunicationRequestViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    serializer_class = CommunicationRequestSerializer
    permission_classes = (FHIRApiCommunicationRequestPermissions,)

    def get_queryset(self):
        return Feedback.get_queryset(None, self.request.user)


class CoverageEligibilityRequestViewSet(BaseFHIRView, mixins.CreateModelMixin, GenericViewSet):
    queryset = Insuree.filter_queryset()
    serializer_class = eval(Config.get_serializer())
    permission_classes = (FHIRApiCoverageEligibilityRequestPermissions,)

    def get_queryset(self):
        return Insuree.get_queryset(None, self.request.user)
    
  
class CoverageRequestQuerySet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin,mixins.UpdateModelMixin,mixins.CreateModelMixin,GenericViewSet):
    lookup_field = 'uuid'
    serializer_class = CoverageSerializer
    permission_classes = (FHIRApiCoverageRequestPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset() 
        queryset.prefetch_related('services')
        refDate = request.GET.get('refDate')
        refEndDate = request.GET.get('refEndDate')
        identifier = request.GET.get("identifier")
        if identifier:
            queryset = queryset.filter(chf_id=identifier)
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from')
            if refDate != None:
                isValidDate = True
                try :
                    datevar = datetime.datetime.strptime(refDate, "%Y-%m-%d").date()
                except ValueError :
                    isValidDate = False
                queryset = queryset.filter(validity_from__gte=datevar)
            if refEndDate != None:
                isValidDate = True
                try :
                    datevar = datetime.datetime.strptime(refEndDate, "%Y-%m-%d").date()
                except ValueError :
                    isValidDate = False
                queryset = queryset.filter(validity_from__lt=datevar)

        serializer = CoverageSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        return Policy.get_queryset(None, self.request.user)


class ContractViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    serializer_class = ContractSerializer
    permission_classes = (FHIRApiCoverageRequestPermissions,)

    def list(self, request, *args, **kwargs):
        #queryset = self.get_queryset() 
        queryset =   self.get_queryset().select_related('product').select_related('officer')\
            .select_related('family__head_insuree').select_related('family__location')\
            .prefetch_related(Prefetch('insuree_policies', queryset=InsureePolicy.objects.filter(validity_to__isnull=True).select_related('insuree')))
        refDate = request.GET.get('refDate')
        refEndDate = request.GET.get('refEndDate')
        identifier = request.GET.get("identifier")
        if identifier:
            queryset = queryset.filter(chf_id=identifier)
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from')
            if refDate != None:
                isValidDate = True
                try :
                    datevar = datetime.datetime.strptime(refDate, "%Y-%m-%d").date()
                except ValueError :
                    isValidDate = False
                queryset = queryset.filter(validity_from__gte=datevar)
            if refEndDate != None:
                isValidDate = True
                try :
                    datevar = datetime.datetime.strptime(refEndDate, "%Y-%m-%d").date()
                except ValueError :
                    isValidDate = False
                queryset = queryset.filter(validity_from__lt=datevar)

        serializer = ContractSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        return Policy.get_queryset(None, self.request.user)


class MedicationViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    serializer_class = MedicationSerializer
    permission_classes = (FHIRApiMedicationPermissions,)

    def get_queryset(self):
        return Item.get_queryset(None, self.request.user)


class ConditionViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    lookup_field = 'id'
    serializer_class = ConditionSerializer
    permission_classes = (FHIRApiConditionPermissions,)

    def get_queryset(self):
        return Diagnosis.get_queryset(None, self.request.user)


class ActivityDefinitionViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    serializer_class = ActivityDefinitionSerializer
    permission_classes = (FHIRApiActivityDefinitionPermissions,)

    def get_queryset(self):
        return Service.get_queryset(None, self.request.user)


class HealthcareServiceViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    serializer_class = HealthcareServiceSerializer
    permission_classes = (FHIRApiHealthServicePermissions,)

    def get_queryset(self):
        return HealthFacility.get_queryset(None, self.request.user)
