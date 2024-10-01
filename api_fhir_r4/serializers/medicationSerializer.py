import copy
import uuid

from medical.models import Item

from api_fhir_r4.converters import MedicationConverter
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.serializers import BaseFHIRSerializer

class MedicationSerializer(BaseFHIRSerializer):
    fhirConverter = MedicationConverter

    def create(self, validated_data):
        imis_medication = Item(**validated_data)
        imis_medication.audit_user_id = self.get_audit_user_id()
        filters = {}
        if imis_medication.id:
            filters['id'] = imis_medication.id
        if imis_medication.uuid:
            filters['uuid'] = imis_medication.uuid 
        if imis_medication.code and not filters:
            filters['code'] = imis_medication.code
            filters['validity_to__isnull'] = True
        
        instance = Item.objects.filter(**filters).first()
        if instance:
            raise ValueError(f"cannot create an already existing object, filters: {filters}")
        imis_medication.audit_user_id = self.get_audit_user_id()
        imis_medication.save()
        return imis_medication
 

    def update(self, instance, validated_data):
        imis_medication = Item(**validated_data)
        imis_medication.audit_user_id = self.get_audit_user_id()
        filters = {}
        if imis_medication.id:
            filters['id'] = imis_medication.id
        if imis_medication.uuid:
            filters['uuid'] = imis_medication.uuid 
        if imis_medication.code and not filters:
            filters['code'] = imis_medication.code
            filters['validity_to__isnull'] = True
        
        instance = Item.objects.filter(**filters).first()
        if not instance:
            raise ValueError(f"cannot update a not found object, filters: {filters}")
        instance.audit_user_id = self.get_audit_user_id()
        instance.save_history()
        imis_medication.id = instance.id
        imis_medication.uuid = instance.uuid
        imis_medication.code = instance.code
        imis_medication.save()
        return imis_medication