from django.utils.translation import gettext
from location.models import HealthFacility, Location, HealthFacilityCatchment

from api_fhir_r4.configurations import GeneralConfiguration, R4IdentifierConfig, R4LocationConfig
from api_fhir_r4.converters import BaseFHIRConverter, ReferenceConverterMixin
from api_fhir_r4.converters.locationConverter import LocationConverter
from fhir.resources.healthcareservice import HealthcareService as FHIRHealthcareService
from api_fhir_r4.models.imisModelEnums import ImisHfLevel
from api_fhir_r4.utils import TimeUtils, DbManagerUtils


class HealthcareServiceConverter(BaseFHIRConverter, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_hf, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_hcs = FHIRHealthcareService.construct()
        cls.build_fhir_pk(fhir_hcs, imis_hf, reference_type)
        cls.build_fhir_healthcare_service_identifier(fhir_hcs, imis_hf)
        cls.build_fhir_healthcare_service_name(fhir_hcs, imis_hf)
        cls.build_fhir_healthcare_service_category(fhir_hcs, imis_hf)
        cls.build_fhir_healthcare_service_extra_details(fhir_hcs, imis_hf)
        cls.build_fhir_healthcare_service_telecom(fhir_hcs, imis_hf)
        cls.build_fhir_location_reference(fhir_hcs, imis_hf, reference_type=reference_type)
        cls.build_fhir_healthcare_service_program(fhir_hcs, imis_hf)
        cls.build_fhir_healthcare_service_specialty(fhir_hcs, imis_hf)
        cls.build_fhir_healthcare_service_type(fhir_hcs, imis_hf)
        cls.build_fhir_healthcare_service_coverage_area(fhir_hcs, imis_hf, reference_type=reference_type)
        return fhir_hcs

    @classmethod
    def to_imis_obj(cls, fhir_hcs, audit_user_id):
        errors = []
        fhir_hcs = FHIRHealthcareService(**fhir_hcs)
        imis_hf = cls.createDefaultHealthFacility(audit_user_id)
        cls.build_imis_hf_identiftier(imis_hf, fhir_hcs, errors)
        cls.build_imis_location_identiftier(imis_hf, fhir_hcs, errors)
        cls.build_imis_hf_name(imis_hf, fhir_hcs, errors)
        cls.build_imis_hf_level(imis_hf, fhir_hcs, errors)
        cls.build_imis_hf_address(imis_hf, fhir_hcs)
        cls.build_imis_hf_contacts(imis_hf, fhir_hcs)
        cls.build_imis_legal_form(imis_hf, fhir_hcs, errors)
        cls.build_imis_sub_level(imis_hf, fhir_hcs, errors)
        cls.build_imis_care_type(imis_hf, fhir_hcs, errors)
        cls.check_errors(errors)
        return imis_hf

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_facility_id_type()

    @classmethod
    def get_reference_obj_uuid(cls, imis_hf: HealthFacility):
        return imis_hf.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_hf: HealthFacility):
        return imis_hf.id

    @classmethod
    def get_reference_obj_code(cls, imis_hf: HealthFacility):
        return imis_hf.code

    @classmethod
    def get_fhir_resource_type(cls):
        return FHIRHealthcareService

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        healthfacility_uuid = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(HealthFacility, uuid=healthfacility_uuid)

    @classmethod
    def createDefaultHealthFacility(cls, audit_user_id):
        imis_hf = HealthFacility()
        # TODO legalForm isn't covered because that value is missing in the model (value need to be nullable in DB)
        # TODO LocationId isn't covered because that value is missing in the model (value need to be nullable in DB)
        imis_hf.offline = GeneralConfiguration.get_default_value_of_location_offline_attribute()
        imis_hf.care_type = GeneralConfiguration.get_default_value_of_location_care_type()
        imis_hf.validity_from = TimeUtils.now()
        imis_hf.audit_user_id = audit_user_id
        return imis_hf

    @classmethod
    def build_fhir_healthcare_service_identifier(cls, fhir_location, imis_hf):
        identifiers = []
        cls.build_all_identifiers(identifiers, imis_hf)
        fhir_location.identifier = identifiers

    @classmethod
    def build_fhir_hf_code_identifier(cls, identifiers, imis_hf):
        if imis_hf is not None:
            identifier = cls.build_fhir_identifier(imis_hf.code,
                                                   R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                   R4IdentifierConfig.get_fhir_facility_id_type())
            identifiers.append(identifier)

    @classmethod
    def build_imis_hf_identiftier(cls, imis_hf, fhir_location, errors):
        value = cls.get_fhir_identifier_by_code(fhir_location.identifier,
                                                R4IdentifierConfig.get_fhir_facility_id_type())
        if value:
            imis_hf.code = value
        cls.valid_condition(imis_hf.code is None, gettext('Missing hf code'), errors)

    @classmethod
    def build_imis_location_identiftier(cls, imis_hf, fhir_location, errors):
        value = cls.get_fhir_identifier_by_code(fhir_location.identifier,
                                                R4IdentifierConfig.get_fhir_facility_id_type())
        # TODO - fix assigning location in HF
        if value:
            imis_hf.location.code = value
        cls.valid_condition(imis_hf.location.code is None, gettext('Missing location code'), errors)

    @classmethod
    def build_fhir_healthcare_service_name(cls, fhir_hcs, imis_hf):
        fhir_hcs.name = imis_hf.name

    @classmethod
    def build_imis_hf_name(cls, imis_hf, fhir_hcs, errors):
        name = fhir_hcs.name
        if not cls.valid_condition(name is None,
                                   gettext('Missing patient `name` attribute'), errors):
            imis_hf.name = name

    @classmethod
    def build_fhir_healthcare_service_category(cls, fhir_hcs, imis_hf):
        code = ""
        text = ""
        if imis_hf.level == ImisHfLevel.HEALTH_CENTER.value:
            code = R4LocationConfig.get_fhir_code_for_health_center()
            text = "Hospital center"
        elif imis_hf.level == ImisHfLevel.HOSPITAL.value:
            code = R4LocationConfig.get_fhir_code_for_hospital()
            text = "Hospital"
        elif imis_hf.level == ImisHfLevel.DISPENSARY.value:
            code = R4LocationConfig.get_fhir_code_for_dispensary()
            text = "Dispensary"

        fhir_hcs.category = \
            [cls.build_codeable_concept(code, R4LocationConfig.get_fhir_location_site_type_system(), text=text)]

    @classmethod
    def build_imis_hf_level(cls, imis_hf, fhir_hcs, errors):
        location_type = fhir_hcs.category
        if not cls.valid_condition(location_type is None,
                                   gettext('Missing patient `type` attribute'), errors):
            for maritalCoding in location_type.coding:
                if maritalCoding.system == R4LocationConfig.get_fhir_location_site_type_system():
                    code = maritalCoding.code
                    if code == R4LocationConfig.get_fhir_code_for_health_center():
                        imis_hf.level = ImisHfLevel.HEALTH_CENTER.value
                    elif code == R4LocationConfig.get_fhir_code_for_hospital():
                        imis_hf.level = ImisHfLevel.HOSPITAL.value
                    elif code == R4LocationConfig.get_fhir_code_for_dispensary():
                        imis_hf.level = ImisHfLevel.DISPENSARY.value

            cls.valid_condition(imis_hf.level is None, gettext('Missing hf level'), errors)

    @classmethod
    def build_fhir_healthcare_service_extra_details(cls, fhir_hcs, imis_hf):
        fhir_hcs.extraDetails = imis_hf.address

    @classmethod
    def build_imis_hf_address(cls, imis_hf, fhir_hcs):
        address = fhir_hcs.extraDetails
        if address is not None:
            if address.type == 'physical':
                imis_hf.address = address.text

    @classmethod
    def build_fhir_healthcare_service_telecom(cls, fhir_hcs, imis_hf):
        telecom = []
        if imis_hf.phone is not None and imis_hf.phone != "":
            phone = HealthcareServiceConverter.build_fhir_contact_point(imis_hf.phone, 'phone',
                                                               "home")
            telecom.append(phone)
        if imis_hf.fax is not None and imis_hf.fax != "":
            fax = HealthcareServiceConverter.build_fhir_contact_point(imis_hf.fax, 'fax',
                                                             "home")
            telecom.append(fax)
        if imis_hf.email is not None and imis_hf.email != "":
            email = HealthcareServiceConverter.build_fhir_contact_point(imis_hf.email, 'email',
                                                               "home")
            telecom.append(email)
        fhir_hcs.telecom = telecom

    @classmethod
    def build_imis_hf_contacts(cls, imis_hf, fhir_hcs):
        telecom = fhir_hcs.telecom
        if telecom is not None:
            for contact_point in telecom:
                if contact_point.system == 'phone':
                    imis_hf.phone = contact_point.value
                elif contact_point.system == 'fax':
                    imis_hf.fax = contact_point.value
                elif contact_point.system == 'email':
                    imis_hf.email = contact_point.value

    @classmethod
    def build_fhir_location_reference(cls, fhir_hcs, imis_hf, reference_type):
        if imis_hf.location is not None:
            fhir_hcs.location = [
                LocationConverter.build_fhir_resource_reference(imis_hf.location, reference_type=reference_type)]

    @classmethod
    def build_fhir_healthcare_service_program(cls, fhir_hcs, imis_hf):
        fhir_hcs.program = [cls.build_codeable_concept(imis_hf.legal_form.code, text=imis_hf.legal_form.legal_form)]

    @classmethod
    def build_imis_legal_form(cls, imis_hf, fhir_hcs, errors):
        code = fhir_hcs.program.coding
        text = fhir_hcs.program.text
        if not cls.valid_condition(code and text is None,
                                   gettext('Missing healthcare service `legal form` attribute'), errors):
            imis_hf.legal_form.code = code
            imis_hf.legal_form.legal_form = text

    @classmethod
    def build_fhir_healthcare_service_specialty(cls, fhir_hcs, imis_hf):
        if imis_hf.sub_level is not None:
            fhir_hcs.specialty = [cls.build_codeable_concept(imis_hf.sub_level.code,
                                                             text=imis_hf.sub_level.health_facility_sub_level)]

    @classmethod
    def build_imis_sub_level(cls, imis_hf, fhir_hcs, errors):
        code = fhir_hcs.specialty.coding
        text = fhir_hcs.specialty.text
        if not cls.valid_condition(code and text is None,
                                   gettext('Missing healthcare service `legal form` attribute'), errors):
            imis_hf.sub_level.code = code
            imis_hf.sub_level.health_facility_sub_level = text

    @classmethod
    def build_fhir_healthcare_service_type(cls, fhir_hcs, imis_hf):
        code = ""
        text = ""
        if imis_hf.care_type == HealthFacility.CARE_TYPE_IN_PATIENT:
            code = R4LocationConfig.get_fhir_code_for_in_patient()
            text = "In-patient"
        elif imis_hf.care_type == HealthFacility.CARE_TYPE_OUT_PATIENT:
            code = R4LocationConfig.get_fhir_code_for_out_patient()
            text = "Out-patient"
        elif imis_hf.care_type == HealthFacility.CARE_TYPE_BOTH:
            code = R4LocationConfig.get_fhir_code_for_both()
            text = "Both"

        fhir_hcs.type = \
            [cls.build_codeable_concept(code, R4LocationConfig.get_fhir_hf_service_type_system(), text=text)]

    @classmethod
    def build_imis_care_type(cls, imis_hf, fhir_hcs, errors):
        care_type = fhir_hcs.type
        if not cls.valid_condition(care_type is None,
                                   gettext('Missing hf `care type` attribute'), errors):
            for maritalCoding in care_type.coding:
                if maritalCoding.system == R4LocationConfig.get_fhir_hf_service_type_system():
                    code = maritalCoding.code
                    if code == R4LocationConfig.get_fhir_code_for_in_patient():
                        imis_hf.care_type = HealthFacility.CARE_TYPE_IN_PATIENT
                    elif code == R4LocationConfig.get_fhir_code_for_out_patient():
                        imis_hf.care_type = HealthFacility.CARE_TYPE_OUT_PATIENT
                    elif code == R4LocationConfig.get_fhir_code_for_both():
                        imis_hf.care_type = HealthFacility.CARE_TYPE_BOTH

            cls.valid_condition(imis_hf.care_type is None, gettext('Missing hf care type'), errors)

    @classmethod
    def build_fhir_healthcare_service_coverage_area(cls, fhir_hcs, imis_hf, reference_type):
        imis_hf_catchments = HealthFacilityCatchment.objects\
            .filter(health_facility=imis_hf) \
            .select_related("location")\
            .values("location")
        for catchment in imis_hf_catchments:
            location = Location.objects.filter(id=catchment["location"])
            fhir_hcs.coverageArea.append(
                LocationConverter.build_fhir_resource_reference(location[0], reference_type=reference_type))
