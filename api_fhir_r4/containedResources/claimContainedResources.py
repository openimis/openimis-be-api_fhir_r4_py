from typing import Dict, Type
from api_fhir_r4.containedResources.containedResources import (
    AbstractContainedResourceCollection,
    ContainedResourceDefinition,
)

from api_fhir_r4.serializers.baseSerializer import BaseFHIRSerializer
from api_fhir_r4.serializers.patientSerializer import PatientSerializer
from api_fhir_r4.serializers.groupSerializer import GroupSerializer
from api_fhir_r4.serializers.healthFacilityOrganisationSerializer import HealthFacilityOrganisationSerializer
from api_fhir_r4.serializers.claimAdminPractitionerSerializer import ClaimAdminPractitionerSerializer
from api_fhir_r4.serializers.medicationSerializer import MedicationSerializer
from api_fhir_r4.serializers.activityDefinitionSerializer import ActivityDefinitionSerializer
from api_fhir_r4.serializers.claimAdminPractitionerRoleSerializer import ClaimAdminPractitionerRoleSerializer
from medical.models import Item, Service


class ClaimContainedResources(AbstractContainedResourceCollection):
    @classmethod
    def _definitions_for_serializers(
        cls,
    ) -> Dict[Type[BaseFHIRSerializer], ContainedResourceDefinition]:
        return {
            PatientSerializer: ContainedResourceDefinition("insuree", "Patient"),
            GroupSerializer: ContainedResourceDefinition(
                "insuree",
                "Group",
                lambda model, field: model.__getattribute__(field).family,
            ),
            HealthFacilityOrganisationSerializer: ContainedResourceDefinition(
                "health_facility", "Organization"
            ),
            ClaimAdminPractitionerSerializer: ContainedResourceDefinition(
                "admin", "Practitioner"
            ),
            ClaimAdminPractitionerRoleSerializer: ContainedResourceDefinition(
                "admin", "PractitionerRole"
            ),
            MedicationSerializer: ContainedResourceDefinition(
                "items",
                "Medication",
                lambda model, field: [
                    item.item
                    for item in model.__getattribute__(field).filter(*Item.filter_validity())
                ],
            ),
            ActivityDefinitionSerializer: ContainedResourceDefinition(
                "services",
                "ActivityDefinition",
                lambda model, field: [
                    service.service
                    for service in model.__getattribute__(field).filter(
                        *Service.filter_validity()
                    )
                ],
            ),
        }
