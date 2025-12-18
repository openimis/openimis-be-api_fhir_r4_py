from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from openIMIS.openimisapps import openimis_apps

from api_fhir_r4.views import LoginView, fhir as fhir_viewsets

imis_modules = openimis_apps()

router = DefaultRouter()
router.register(r'login', LoginView, basename="login")
# Subscription endpoint now handled by standalone fhir_R4_subscription app
# router.register(r'Subscription', fhir_viewsets.SubscriptionViewSet, basename='Subscription_R4')

# register endpoint related to Product module if used
# InsurancePlan endpoint moved to standalone fhir_R4_Insurance app
# if 'product' in imis_modules:
#     router.register(r'InsurancePlan', fhir_viewsets.ProductViewSet, basename="InsurancePlan_R4")

# Location endpoints are moved to standalone fhir_R4_Location app

"""
Insuree/Patient endpoints moved to standalone fhir_R4_Patient app.
Group and related code systems moved to standalone fhir_R4_Group app.
We keep CoverageEligibilityRequest here.
"""
if 'insuree' in imis_modules:
    router.register(
        r'CoverageEligibilityRequest', fhir_viewsets.CoverageEligibilityRequestViewSet,
        basename="CoverageEligibilityRequest_R4"
    )

# register endpoints related to medical module
if 'medical' in imis_modules:
    router.register(r'Medication', fhir_viewsets.MedicationViewSet, basename="Medication_R4")
    router.register(r'ActivityDefinition', fhir_viewsets.ActivityDefinitionViewSet, basename="ActivityDefinition_R4")

# register all endpoints related to c based on c
if 'claim' in imis_modules:
    router.register(r'Claim', fhir_viewsets.ClaimViewSet, basename="Claim_R4")
    router.register(r'ClaimResponse', fhir_viewsets.ClaimResponseViewSet, basename="ClaimResponse_R4")
    router.register(r'PractitionerRole', fhir_viewsets.PractitionerRoleViewSet, basename="PractitionerRole_R4")
    router.register(r'Practitioner', fhir_viewsets.PractitionerViewSet, basename="Practitioner_R4")
    # Communication endpoints moved to standalone fhir_R4_Communication app
    # code system for openimis medication
    router.register(r'CodeSystem/diagnosis', fhir_viewsets.CodeSystemOpenIMISDiagnosisViewSet,
                    basename="CodeSystem/diagnosis_R4")

# register endpoint for policy if used
if 'policy' in imis_modules:
    router.register(r'Coverage', fhir_viewsets.CoverageRequestQuerySet, basename="Coverage_R4")
    router.register(r'Contract', fhir_viewsets.ContractViewSet, basename="Contract_R4")

# register endpoint for policy holder if used
if 'policyholder' in imis_modules:
    router.register(r'Organization', fhir_viewsets.OrganisationViewSet, basename="Organisation_R4")
    router.register(r'CodeSystem/organization-ph-legal-form', fhir_viewsets.CodeSystemOrganizationPHLegalFormViewSet,
                    basename="CodeSystem/organization-ph-legal-form_R4")
    router.register(r'CodeSystem/organization-ph-activity', fhir_viewsets.CodeSystemOrganizationPHActivityViewSet,
                    basename="CodeSystem/organization-ph-activity_R4")

# register endpoint for policy holder if used
if 'invoice' in imis_modules:
    router.register(r'Invoice', fhir_viewsets.InvoiceViewSet, basename="Invoice_R4")
    router.register(r'PaymentNotice', fhir_viewsets.PaymentNoticeViewSet, basename="PaymentNotice_R4")

urlpatterns = [
    path('', include(router.urls)),
    path('', include('fhir_R4_Communication.urls')),
    path('docs/', SpectacularAPIView.as_view(), name='docs'),
    path('docs/swagger/', SpectacularSwaggerView.as_view(url_name='docs'), name='swagger-ui'),
    path('docs/redoc/', SpectacularRedocView.as_view(url_name='docs'), name='redoc'),
]
