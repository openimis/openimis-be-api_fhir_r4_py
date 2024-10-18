from typing import Dict, Type
from core.utils import filter_validity
from api_fhir_r4.containedResources.containedResources import AbstractContainedResourceCollection, \
    ContainedResourceDefinition
from api_fhir_r4.serializers import BaseFHIRSerializer, PatientSerializer, GroupSerializer, \
    HealthFacilityOrganisationSerializer, ClaimAdminPractitionerSerializer, MedicationSerializer, \
    ActivityDefinitionSerializer, ClaimAdminPractitionerRoleSerializer


class ClaimContainedResources(AbstractContainedResourceCollection):
    @classmethod
    def _definitions_for_serializers(cls) -> Dict[Type[BaseFHIRSerializer], ContainedResourceDefinition]:
        return {
            PatientSerializer: ContainedResourceDefinition('insuree', 'Patient'),
            GroupSerializer: ContainedResourceDefinition(
                'insuree', 'Group',
                lambda model, field: model.__getattribute__(field).family
            ),
            HealthFacilityOrganisationSerializer: ContainedResourceDefinition('health_facility', 'Organization'),
            ClaimAdminPractitionerSerializer: ContainedResourceDefinition('admin', 'Practitioner'),
            ClaimAdminPractitionerRoleSerializer: ContainedResourceDefinition('admin', 'PractitionerRole'),
            MedicationSerializer: ContainedResourceDefinition(
                'items', 'Medication',
                lambda model, field: [
                    item.item for item in model.__getattribute__(field).filter(*filter_validity())
                ]
            ),
            ActivityDefinitionSerializer: ContainedResourceDefinition(
                'services', 'ActivityDefinition',
                lambda model, field: [
                    service.service for service in model.__getattribute__(field).filter(*filter_validity())
                ]
            ),
        }
