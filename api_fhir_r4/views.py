from api_fhir_r4.converters import OperationOutcomeConverter
from api_fhir_r4.permissions import FHIRApiClaimPermissions, FHIRApiCoverageEligibilityRequestPermissions, \
    FHIRApiCoverageRequestPermissions, FHIRApiCommunicationRequestPermissions, FHIRApiPractitionerPermissions, \
    FHIRApiHFPermissions, FHIRApiInsureePermissions, FHIRApiMedicationPermissions, FHIRApiConditionPermissions, \
    FHIRApiActivityDefinitionPermissions, FHIRApiHealthServicePermissions
from claim.models import ClaimAdmin, Claim, Feedback, ClaimItem ,ClaimService
from django.db.models import OuterRef, Exists
from insuree.models import Insuree, InsureePolicy,Family
from policyholder.models import PolicyHolder
from location.models import HealthFacility, Location
from policy.models import Policy
from medical.models import Item, Diagnosis, Service
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import parser_classes,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
import os
from api_fhir_r4.paginations import FhirBundleResultsSetPagination
from api_fhir_r4.permissions import FHIRApiPermissions
from api_fhir_r4.configurations import R4CoverageEligibilityConfiguration as Config,GeneralConfiguration
from api_fhir_r4.serializers import PatientSerializer, LocationSerializer, LocationSiteSerializer, PractitionerRoleSerializer, \
    PractitionerSerializer, ClaimSerializer, CoverageEligibilityRequestSerializer, \
    PolicyCoverageEligibilityRequestSerializer, ClaimResponseSerializer, CommunicationRequestSerializer, \
    MedicationSerializer, ConditionSerializer, ActivityDefinitionSerializer, HealthcareServiceSerializer ,ContractSerializer,GroupSerializer,\
    OrganisationSerializer
from api_fhir_r4.serializers.coverageSerializer import CoverageSerializer
from django.db.models import Prefetch
from rest_framework.decorators import api_view
import datetime
from rest_framework.parsers import JSONParser
import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth
from django.views import View
from policy.services import ByInsureeRequest, ByInsureeService, ByInsureeResponse

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


class BaseFHIRView(APIView):
    pagination_class = FhirBundleResultsSetPagination
    permission_classes = (FHIRApiPermissions,)
    authentication_classes = [CsrfExemptSessionAuthentication] + APIView.settings.DEFAULT_AUTHENTICATION_CLASSES


class InsureeViewSet(BaseFHIRView, viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = PatientSerializer
    # permission_classes = (FHIRApiInsureePermissions,)

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
                    return Response(result.toDict(), status.HTTP_400_BAD_REQUEST)
                has_claim_in_range = Claim.objects\
                    .filter(date_claimed__gte=claim_parse_dated)\
                    .filter(insuree_id=OuterRef("id"))\
                    .values("id")
                queryset = queryset.annotate(has_claim_in_range=Exists(has_claim_in_range)).filter(has_claim_in_range=True)

        serializer = PatientSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    
    def get_queryset(self):
        return Insuree.objects
    
class GroupViewSet(BaseFHIRView, viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = GroupSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = GroupSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        return Family.objects.all().order_by('validity_from')

class OrganisationViewSet(BaseFHIRView, viewsets.ModelViewSet):
    lookup_field = 'code'
    serializer_class = OrganisationSerializer
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = OrganisationSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)
    
    def get_queryset(self):
        return PolicyHolder.objects.all().order_by('date_created')
    
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
        #return Location.get_queryset(None, self.request.user)
        if physicalType == 'si':
            return HealthFacility.objects.select_related('location').select_related('sub_level').select_related('legal_form')
        else:
            return Location.objects.select_related('parent')
        
   

class PractitionerRoleViewSet(BaseFHIRView, viewsets.ModelViewSet):
    lookup_field = 'uuid'
    serializer_class = PractitionerRoleSerializer
    #permission_classes = (FHIRApiPractitionerPermissions,)

    def list(self, request, *args, **kwargs):
        identifier = request.GET.get("identifier")
        queryset = self.get_queryset()
        if identifier:
            queryset = queryset.filter(code=identifier)
        else:
            queryset = queryset.filter(validity_to__isnull=True).order_by('validity_from'
                                                                          )
        serializer = PractitionerRoleSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def perform_destroy(self, instance):
        instance.health_facility_id = None
        instance.save()

    def get_queryset(self):
        #return ClaimAdmin.get_queryset(None, self.request.user)
        return ClaimAdmin.objects.all()


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
        #return ClaimAdmin.get_queryset(None, self.request.user)
        return ClaimAdmin.filter_queryset(None)

class ClaimViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin,
                   mixins.CreateModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    serializer_class = ClaimSerializer
    #permission_classes = (FHIRApiClaimPermissions,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset().select_related('insuree').select_related('health_facility').select_related('icd')\
            .select_related('icd_1').select_related('icd_2').select_related('icd_3').select_related('icd_4')\
            .prefetch_related(Prefetch('items', queryset=ClaimItem.objects.filter(validity_to__isnull=True)))\
            .prefetch_related(Prefetch('services', queryset=ClaimService.objects.filter(validity_to__isnull=True)))\
            .prefetch_related(Prefetch('insuree__insuree_policies', queryset=InsureePolicy.objects.filter(validity_to__isnull=True).select_related("policy"))) #.filter(start_date__lte=date_from , expiry_date__gte=date_from)
        refDate = request.GET.get('refDate')
        identifier = request.GET.get("identifier")
        patient = request.GET.get("patient")
        if identifier is not None:
            queryset = queryset.filter(identifier=identifier)
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
        serializer = ClaimSerializer(self.paginate_queryset(queryset), many=True)
        return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        #return Claim.get_queryset(None, self.request.user)
        return Claim.objects


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
    # PolicyCoverageEligibilityRequestSerializer
    permission_classes = (FHIRApiCoverageEligibilityRequestPermissions,)
    def get_queryset(self):
        return Insuree.get_queryset(None, self.request.user)
    
        
class PatientEligibility(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request, format=None):
        data=request.data
        patient=data['patient']['reference'].rsplit('/',1)
        url=os.environ.get('OPEHNHIM_URL')
        technical_user =os.environ.get('OPEHNHIM_URL')
        password =os.environ.get('OPEHNHIM_PASSWORD')
        try:
            response = requests.post(url+'Eligibilty',json=data,auth=HTTPBasicAuth(technical_user,password))
            response.raise_for_status()
            if response.status_code == 200:
                eligibility_request=ByInsureeRequest(chf_id=patient[1])
                try:
                    response = ByInsureeService(request.user).request(eligibility_request)
                except Exception as e:
                    pass  
                return Response(PolicyCoverageEligibilityRequestSerializer(response).data)
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            eligibility_request =ByInsureeRequest(chf_id=patient[1])
            try:
                response = ByInsureeService(request.user).request(eligibility_request)
            except Exception as e:
                pass  
            return Response(PolicyCoverageEligibilityRequestSerializer(response).data)

        
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
        return Policy.objects
        #return Policy.get_queryset(None, self.request.user)

class ContractViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
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
        return Policy.objects

class MedicationViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    lookup_field = 'uuid'
    serializer_class = MedicationSerializer
    permission_classes = (FHIRApiMedicationPermissions,)

    def get_queryset(self):
        return Item.get_queryset(None, self.request.user)


class ConditionViewSet(BaseFHIRView, mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
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
        #return HealthFacility.get_queryset(None, self.request.user)
        return HealthFacility.get_queryset(None, self.request.user)
