from api_fhir_r4 import views
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from openIMIS.openimisapps import *


imis_modules = openimis_apps()


router = DefaultRouter()
router.register(r'login', views.LoginView, basename="login")
# register endpojnt related to Location module if used
if 'location' in imis_modules:
    router.register(r'Location', views.LocationViewSet, basename="Location_R4")
    router.register(r'HealthcareService', views.HealthcareServiceViewSet, basename="HealthcareService_R4")
# register endpoint for insuree if used
if 'insuree' in imis_modules:
    router.register(r'Patient', views.InsureeViewSet, basename="Patient_R4")
    router.register(r'Group', views.GroupViewSet, basename="Group_R4")
    router.register(
        r'CoverageEligibilityRequest', views.CoverageEligibilityRequestViewSet, basename="CoverageEligibilityRequest_R4"
    )
# register endpoints related to medical module
if 'medical' in imis_modules:
    router.register(r'Medication', views.MedicationViewSet, basename="Medication_R4")
    router.register(r'Condition', views.ConditionViewSet, basename="Condition_R4")
    router.register(r'ActivityDefinition', views.ActivityDefinitionViewSet, basename="ActivityDefinition_R4")
# register all endpoints related to claim based on claim
if 'claim' in imis_modules:
    router.register(r'Claim', views.ClaimViewSet, basename="Claim_R4")
    router.register(r'ClaimResponse', views.ClaimResponseViewSet, basename="ClaimResponse_R4")
    router.register(r'PractitionerRole', views.PractitionerRoleViewSet, basename="PractitionerRole_R4")
    router.register(r'Practitioner', views.PractitionerViewSet, basename="Practitioner_R4")
    router.register(r'CommunicationRequest', views.CommunicationRequestViewSet, basename="CommunicationRequest_R4")
# register endpoint for policy if used
if 'policy' in imis_modules:
    router.register(r'Coverage', views.CoverageRequestQuerySet, basename="Coverage_R4")
    router.register(r'Contract', views.ContractViewSet, basename="Contract_R4")
# register endpoint for policy holder if used
if 'policyholder' in imis_modules:
    router.register(r'Organisation', views.OrganisationViewSet, basename="Organisation_R4")
urlpatterns = [path('', include(router.urls))]
