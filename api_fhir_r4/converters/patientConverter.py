import json
import urllib
from urllib.parse import urlparse

from django.utils.translation import gettext as _
from fhir.resources.R4B.address import Address

from insuree.models import Insuree, Gender, Education, Profession, Family, \
    InsureePhoto, Relation, IdentificationType
from location.models import Location, HealthFacility
from api_fhir_r4.configurations import R4IdentifierConfig, GeneralConfiguration, R4MaritalConfig
from api_fhir_r4.converters import BaseFHIRConverter, PersonConverterMixin, ReferenceConverterMixin
from api_fhir_r4.converters.groupConverter import GroupConverter
from api_fhir_r4.converters.locationConverter import LocationConverter
from api_fhir_r4.mapping.patientMapping import RelationshipMapping, EducationLevelMapping, \
    PatientProfessionMapping, MaritalStatusMapping, PatientCategoryMapping
from api_fhir_r4.models.imisModelEnums import ImisMaritalStatus
from fhir.resources.R4B.patient import Patient, PatientContact
from fhir.resources.R4B.extension import Extension
from fhir.resources.R4B.attachment import Attachment
from api_fhir_r4.exceptions import FHIRException
from api_fhir_r4.utils import TimeUtils, DbManagerUtils

class PatientConverter(BaseFHIRConverter, PersonConverterMixin, ReferenceConverterMixin):

    @classmethod
    def to_fhir_obj(cls, imis_insuree, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        fhir_patient = Patient.construct()
        cls.build_fhir_pk(fhir_patient, imis_insuree, reference_type)
        cls.build_human_names(fhir_patient, imis_insuree)
        cls.build_fhir_identifiers(fhir_patient, imis_insuree)
        cls.build_fhir_birth_date(fhir_patient, imis_insuree)
        cls.build_fhir_gender(fhir_patient, imis_insuree)
        cls.build_fhir_marital_status(fhir_patient, imis_insuree)
        cls.build_fhir_telecom(fhir_patient, imis_insuree)
        cls.build_fhir_addresses(fhir_patient, imis_insuree, reference_type)
        cls.build_fhir_extentions(fhir_patient, imis_insuree, reference_type)
        cls.build_fhir_contact(fhir_patient, imis_insuree)
        cls.build_fhir_photo(fhir_patient, imis_insuree)
        cls.build_fhir_general_practitioner(fhir_patient, imis_insuree, reference_type)
        return fhir_patient

    @classmethod
    def to_imis_obj(cls, fhir_patient, audit_user_id):
        errors = []
        fhir_patient = Patient(**fhir_patient)
        imis_insuree = cls.createDefaultInsuree(audit_user_id)
        cls.build_imis_names(imis_insuree, fhir_patient, errors)
        cls.build_imis_identifiers(imis_insuree, fhir_patient)
        cls.build_imis_birth_date(imis_insuree, fhir_patient, errors)
        cls.build_imis_gender(imis_insuree, fhir_patient)
        cls.build_imis_marital(imis_insuree, fhir_patient)
        cls.build_imis_contacts(imis_insuree, fhir_patient)
        cls.build_imis_addresses(imis_insuree, fhir_patient)
        cls.build_imis_photo(imis_insuree, fhir_patient, errors)
        cls.build_imis_extentions(imis_insuree, fhir_patient, errors)
        cls.build_imis_family(imis_insuree, fhir_patient, errors)
        cls.build_imis_relationship(imis_insuree, fhir_patient)
        cls.build_imis_general_practitioner(imis_insuree, fhir_patient)
        return imis_insuree

    @classmethod
    def build_fhir_pk(cls, fhir_patient, resource, reference_type: str = None):
        if reference_type == ReferenceConverterMixin.CODE_REFERENCE_TYPE:
            fhir_patient.id = resource.chf_id
        else:
            super().build_fhir_pk(fhir_patient, resource, reference_type)

    @classmethod
    def get_fhir_code_identifier_type(cls):
        return R4IdentifierConfig.get_fhir_generic_type_code()

    @classmethod
    def get_reference_obj_uuid(cls, imis_patient: Insuree):
        return imis_patient.uuid

    @classmethod
    def get_reference_obj_id(cls, imis_patient: Insuree):
        return imis_patient.id

    @classmethod
    def get_reference_obj_code(cls, imis_patient: Insuree):
        return imis_patient.chf_id

    @classmethod
    def build_imis_extentions(cls, imis_insuree, fhir_patient, errors):
        cls._validate_fhir_extension_is_exist(fhir_patient)
        for extension in fhir_patient.extension:
            if extension.url == f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-is-head":
                imis_insuree.head = extension.valueBoolean

            elif extension.url == f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-education-level":
                try:
                    imis_insuree.education = Education.objects.get(id=extension.valueCodeableConcept.coding[0].code)
                except Exception:
                    imis_insuree.education = None

            elif extension.url == f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-profession":
                try:
                    imis_insuree.profession = Profession.objects.get(id=extension.valueCodeableConcept.coding[0].code)
                except Exception:
                    imis_insuree.profession = None

            elif extension.url == f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-card-issued":
                try:
                    imis_insuree.card_issued = extension.valueBoolean
                except Exception:
                    imis_insuree.card_issued = False

            elif extension.url == f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-identification":
                try:
                    for ext in extension.extension:
                        if ext.url == "number":
                            imis_insuree.passport = ext.valueString
                        if ext.url == "type":
                            imis_insuree.type_of_id = IdentificationType.objects.get(code=ext.valueCodeableConcept.coding[0].code)
                except Exception:
                    imis_insuree.passport = None
                    imis_insuree.type_of_id = None
            else:
                pass
        cls._validate_imis_is_head(imis_insuree)
    
    @classmethod
    def get_location_reference(cls, location):
        return location.rsplit('Location/', 1)[1]

    @classmethod
    def get_fhir_resource_type(cls):
        return Patient

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        return DbManagerUtils.get_object_or_none(
            Insuree,
            **cls.get_database_query_id_parameteres_from_reference(reference, 'chf_id'))

    @classmethod
    def createDefaultInsuree(cls, audit_user_id):
        imis_insuree = Insuree()
        # temporary set uuid as None - this will be generated in service create insuree from that module
        imis_insuree.uuid = None
        imis_insuree.head = GeneralConfiguration.get_default_value_of_patient_head_attribute()
        imis_insuree.card_issued = GeneralConfiguration.get_default_value_of_patient_card_issued_attribute()
        imis_insuree.validity_from = TimeUtils.now()
        imis_insuree.audit_user_id = audit_user_id
        return imis_insuree

    @classmethod
    def build_human_names(cls, fhir_patient, imis_insuree):
        name = cls.build_fhir_names_for_person(imis_insuree)
        if type(fhir_patient.name) is not list:
            fhir_patient.name = [name]
        else:
            fhir_patient.name.append(name)

    @classmethod
    def build_imis_names(cls, imis_insuree, fhir_patient, errors):
        cls._validate_fhir_patient_human_name(fhir_patient)
        names = fhir_patient.name
        imis_insuree.last_name, imis_insuree.other_names = cls.build_imis_last_and_other_name(names)
        cls._validate_imis_insuree_human_name(imis_insuree)

    @classmethod
    def build_fhir_identifiers(cls, fhir_patient, imis_insuree):
        identifiers = []
        cls._validate_imis_identifier_code(imis_insuree)
        cls.build_all_identifiers(identifiers, imis_insuree)
        cls.build_fhir_passport_identifier(identifiers, imis_insuree)
        fhir_patient.identifier = identifiers
        cls._validate_fhir_identifier_is_exist(fhir_patient)

    @classmethod
    def build_fhir_code_identifier(cls, identifiers, imis_object: Insuree):
        # Patient don't have code so chfid is used instead as code identifier
        if hasattr(imis_object, 'chf_id'):
            identifiers.append(cls.__build_chfid_identifier(imis_object.chf_id))

    @classmethod
    def __build_chfid_identifier(cls, chfid):
        return cls.build_fhir_identifier(chfid,
                                         R4IdentifierConfig.get_fhir_identifier_type_system(),
                                         R4IdentifierConfig.get_fhir_generic_type_code())

    @classmethod
    def build_imis_identifiers(cls, imis_insuree, fhir_patient):
        insuree_ids = fhir_patient.identifier

        if chf_id := cls.get_fhir_identifier_by_code(insuree_ids, R4IdentifierConfig.get_fhir_generic_type_code()):
            imis_insuree.chf_id = chf_id
        else:
            raise FHIRException("Patient code not provided.")

        if passport := cls.get_fhir_identifier_by_code(insuree_ids, R4IdentifierConfig.get_fhir_passport_type_code()):
            imis_insuree.passport = passport

    @classmethod
    def build_fhir_chfid_identifier(cls, identifiers, imis_insuree):
        cls._validate_imis_identifier_code(imis_insuree)
        identifier = cls.build_fhir_identifier(
            imis_insuree.chf_id,
            R4IdentifierConfig.get_fhir_identifier_type_system(),
            R4IdentifierConfig.get_fhir_generic_type_code()
        )
        identifiers.append(identifier)

    @classmethod
    def build_fhir_passport_identifier(cls, identifiers, imis_insuree):
        if hasattr(imis_insuree, "type_of_id") and imis_insuree.type_of_id is not None:
            pass  # TODO typeofid isn't provided, this section should contain logic used to create passport field based on typeofid
        elif imis_insuree.passport:
            identifier = cls.build_fhir_identifier(imis_insuree.passport,
                                                   R4IdentifierConfig.get_fhir_identifier_type_system(),
                                                   R4IdentifierConfig.get_fhir_passport_type_code())
            identifiers.append(identifier)

    @classmethod
    def build_fhir_birth_date(cls, fhir_patient, imis_insuree):
        from core import datetime
        # check if datetime object
        if isinstance(imis_insuree.dob, datetime.datetime):
            fhir_patient.birthDate = str(imis_insuree.dob.date().isoformat())
        else:
            fhir_patient.birthDate = str(imis_insuree.dob.isoformat())
        
    @classmethod
    def build_imis_family(cls, imis_insuree, fhir_patient, errors):
        # Get UUID from patient group reference related extension
        family = cls.__get_family_from_fhir_patient_extension(fhir_patient)
        if family:
            imis_insuree.family = family

        if family and imis_insuree.head:
            raise FHIRException("Patient assigned to existing family can't be head")

    @classmethod
    def build_imis_link(cls, imis_insuree,fhir_link):
        patient = fhir_link[0].other.reference
        value = patient.rsplit('/',1)[1]
        return value
    
    @classmethod
    def build_imis_relationship(cls, imis_insuree,fhir_patient):
        if fhir_patient.contact:
            for contact in fhir_patient.contact:
                if contact.relationship:
                    relationship_name = None
                    for relationship in contact.relationship:
                        for coding in relationship.coding:
                            if "CodeSystem/patient-contact-relationship" in coding.system:
                                relationship_name = coding.display
                    try:
                        relation = Relation.objects.get(relation=relationship_name)
                        imis_insuree.relationship = relation
                    except:
                        pass
    
    @classmethod
    def build_imis_birth_date(cls, imis_insuree, fhir_patient, errors):
        birth_date = fhir_patient.birthDate
        if not cls.valid_condition(birth_date is None, _('Missing patient `birthDate` attribute'), errors):
            imis_insuree.dob = TimeUtils.str_to_date(birth_date)

    @classmethod
    def build_fhir_gender(cls, fhir_patient, imis_insuree):
        if imis_insuree.gender:
            code = imis_insuree.gender.code
            if code == GeneralConfiguration.get_male_gender_code():
                fhir_patient.gender = "male"
            elif code == GeneralConfiguration.get_female_gender_code():
                fhir_patient.gender = "female"
            elif code == GeneralConfiguration.get_other_gender_code():
                fhir_patient.gender = "other"
        else:
            fhir_patient.gender = "unknown"

    @classmethod
    def build_imis_gender(cls, imis_insuree, fhir_patient):
        gender = fhir_patient.gender
        PatientCategoryMapping.load()
        if gender is not None:
            imis_gender = PatientCategoryMapping.imis_gender_mapping.get(gender)
            imis_insuree.gender = imis_gender

    @classmethod
    def build_fhir_marital_status(cls, fhir_patient, imis_insuree):
        if imis_insuree.marital:
            display = MaritalStatusMapping.marital_status[imis_insuree.marital]
            fhir_patient.maritalStatus = \
                cls.build_codeable_concept(code=imis_insuree.marital,
                                           system=R4MaritalConfig.get_fhir_marital_status_system())
            if len(fhir_patient.maritalStatus.coding) == 1:
                fhir_patient.maritalStatus.coding[0].display = display

    @classmethod
    def build_imis_marital(cls, imis_insuree, fhir_patient):
        marital_status = fhir_patient.maritalStatus
        if marital_status is not None:
            for maritialCoding in marital_status.coding:
                if maritialCoding.system == R4MaritalConfig.get_fhir_marital_status_system():
                    code = maritialCoding.code
                    if code == R4MaritalConfig.get_fhir_married_code():
                        imis_insuree.marital = ImisMaritalStatus.MARRIED.value
                    elif code == R4MaritalConfig.get_fhir_never_married_code():
                        imis_insuree.marital = ImisMaritalStatus.SINGLE.value
                    elif code == R4MaritalConfig.get_fhir_divorced_code():
                        imis_insuree.marital = ImisMaritalStatus.DIVORCED.value
                    elif code == R4MaritalConfig.get_fhir_widowed_code():
                        imis_insuree.marital = ImisMaritalStatus.WIDOWED.value
                    elif code == R4MaritalConfig.get_fhir_unknown_marital_status_code():
                        imis_insuree.marital = ImisMaritalStatus.NOT_SPECIFIED.value

    @classmethod
    def build_fhir_telecom(cls, fhir_patient, imis_insuree):
        fhir_patient.telecom = cls.build_fhir_telecom_for_person(phone=imis_insuree.phone, email=imis_insuree.email)

    @classmethod
    def build_imis_contacts(cls, imis_insuree, fhir_patient):
        imis_insuree.phone, imis_insuree.email = cls.build_imis_phone_num_and_email(fhir_patient.telecom)

    @classmethod
    def build_fhir_addresses(cls, fhir_patient, imis_insuree, reference_type):
        addresses = []

        # If family doesn't have location assigned then use family location
        if imis_insuree.current_village:
            insuree_address = cls._build_insuree_address(imis_insuree, reference_type)
            addresses.append(insuree_address)
        elif imis_insuree.family and imis_insuree.family.location:
            family_address = cls._build_insuree_family_address(imis_insuree.family, reference_type)
            addresses.append(family_address)

        fhir_patient.address = addresses
        cls._validate_fhir_address_details(fhir_patient.address)

    @classmethod
    def build_imis_addresses(cls, imis_insuree, fhir_patient):
        cls._validate_fhir_address_details(fhir_patient.address)

        provided_address = cls.__get_address_by_properties(fhir_patient, type_='physical')

        cls._add_insuree_address(imis_insuree, provided_address)
        if cls._is_patient_head(fhir_patient):
            cls._add_family_address(imis_insuree, provided_address)

    @classmethod
    def _build_imis_current_patient_address(cls, imis_insuree, fhir_patient):
        cls._validate_fhir_address_details(fhir_patient.address)
        if insuree_address := cls.__get_insuree_current_address_from_fhir_patinet(fhir_patient):
            cls._add_insuree_address(imis_insuree, insuree_address)

    @classmethod
    def _build_or_validate_family_address(cls, imis_insuree, fhir_patient):
        if not (fhir_family_address := cls.__get_family_address_from_fhir_patient(fhir_patient)):
            return

        if not (family := cls.__get_family_from_fhir_patient_extension(fhir_patient)):
            cls._add_family_address(imis_insuree, fhir_patient)

    @classmethod
    def _add_insuree_address(cls, imis_insuree, fhir_address):
        imis_insuree.current_village = cls.__get_location_from_address(fhir_address)
        if fhir_address.text:
            imis_insuree.current_address = fhir_address.text

    @classmethod
    def _add_family_address(cls, imis_insuree, fhir_address):
        family_location = cls.__get_location_from_address(fhir_address)
        # Additional attribute for purpose of creating new family
        imis_insuree.family_location = family_location
        if fhir_address.text:
            imis_insuree.family_address = fhir_address.text

    @classmethod
    def build_fhir_extentions(cls, fhir_patient, imis_insuree, reference_type):
        fhir_patient.extension = []

        def build_extension(fhir_patient, imis_insuree, value):
            extension = Extension.construct()
            if value == "head":
                extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-is-head"
                extension.valueBoolean = imis_insuree.head

            elif value == "education.education":
                extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-education-level"
                if hasattr(imis_insuree, "education") and imis_insuree.education is not None:
                    EducationLevelMapping.load()
                    display = EducationLevelMapping.education_level[str(imis_insuree.education.id)]
                    system = "CodeSystem/patient-education-level"
                    extension.valueCodeableConcept = cls.build_codeable_concept(code=str(imis_insuree.education.id), system=system)
                    if len(extension.valueCodeableConcept.coding) == 1:
                        extension.valueCodeableConcept.coding[0].display = display

            elif value == "patient.card.issue":
                extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-card-issued"
                extension.valueBoolean = imis_insuree.card_issued

            elif value == "patient.group.reference":
                extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-group-reference"
                extension.valueReference = GroupConverter\
                    .build_fhir_resource_reference(imis_insuree.family, 'Group', reference_type=reference_type)

            elif value == "patient.identification":
                nested_extension = Extension.construct()
                extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-identification"
                if hasattr(imis_insuree, "type_of_id") and imis_insuree.type_of_id:
                    if hasattr(imis_insuree, "passport") and imis_insuree.passport:
                        # add number extension
                        nested_extension.url = "number"
                        nested_extension.valueString = imis_insuree.passport
                        extension.extension = [nested_extension]
                        # add identifier extension
                        nested_extension = Extension.construct()
                        nested_extension.url = "type"
                        system = "CodeSystem/patient-identification-type"
                        nested_extension.valueCodeableConcept = cls.build_codeable_concept(code=imis_insuree.type_of_id.code, system=system)
                        extension.extension.append(nested_extension)

            else:
                extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/patient-profession"
                if hasattr(imis_insuree, "profession") and imis_insuree.profession is not None:
                    PatientProfessionMapping.load()
                    display = PatientProfessionMapping.patient_profession[str(imis_insuree.profession.id)]
                    system = "CodeSystem/patient-profession"
                    extension.valueCodeableConcept = cls.build_codeable_concept(code=str(imis_insuree.profession.id), system=system)
                    if len(extension.valueCodeableConcept.coding) == 1:
                        extension.valueCodeableConcept.coding[0].display = display

            if type(fhir_patient.extension) is not list:
                fhir_patient.extension = [extension]
            else:
                fhir_patient.extension.append(extension)


        if imis_insuree.head is not None:
            build_extension(fhir_patient, imis_insuree, "head")
        if imis_insuree.education is not None:
            build_extension(fhir_patient, imis_insuree, "education.education")
        if imis_insuree.profession is not None:
            build_extension(fhir_patient, imis_insuree, "profession.profession")
        if imis_insuree.card_issued is not None:
            build_extension(fhir_patient, imis_insuree, "patient.card.issue")
        if imis_insuree.family is not None:
            build_extension(fhir_patient, imis_insuree, "patient.group.reference")
        if imis_insuree.type_of_id is not None and imis_insuree.passport is not None:
            build_extension(fhir_patient, imis_insuree, "patient.identification")

    @classmethod
    def build_fhir_contact(cls, fhir_patient, imis_insuree):
        fhir_contact = PatientContact.construct()
        if imis_insuree.relationship is not None and imis_insuree.family is not None \
                and imis_insuree.family.head_insuree is not None:
            system = "CodeSystem/patient-contact-relationship"
            # map to the fhir value from imis one
            RelationshipMapping.load()
            display = RelationshipMapping.relationship[str(imis_insuree.relationship.id)]
            fhir_contact.relationship = [cls.build_codeable_concept(code=imis_insuree.relationship.id, system=system)]
            fhir_contact.relationship[0].coding[0].display = display
            fhir_contact.name = cls.build_fhir_names_for_person(imis_insuree)

            if type(fhir_patient.contact) is not list:
                fhir_patient.contact = [fhir_contact]
            else:
                fhir_patient.contact.append(fhir_contact)

    @classmethod
    def build_fhir_photo(cls, fhir_patient, imis_insuree):
        if imis_insuree.photo and imis_insuree.photo.folder and imis_insuree.photo.filename:
            # HOST is taken from global variable used in the docker initialization
            # If URL root is not explicitly given in the settings 'localhost' is used
            # (if value is empty validation exception is raised).
            abs_url = GeneralConfiguration.get_host_domain().split('http://')[1] or 'localhost'
            domain = abs_url
            photo_uri = cls.__build_photo_uri(imis_insuree)
            photo = Attachment.construct()
            parsed = urllib.parse.urlunparse(('http', domain, photo_uri, None, None, None))
            photo.url = parsed
            photo.creation = imis_insuree.photo.date.isoformat()
            photo.contentType = imis_insuree.photo.filename[imis_insuree.photo.filename.rfind('.') + 1:]
            photo.title = imis_insuree.photo.filename
            if type(fhir_patient.photo) is not list:
                fhir_patient.photo = [photo]
            else:
                fhir_patient.photo.append(photo)

    @classmethod
    def build_imis_photo(cls, imis_insuree, fhir_patient, errors):
        if fhir_patient.photo and len(fhir_patient.photo) > 0:
            cls._validate_fhir_photo(fhir_patient)
            if fhir_patient.photo[0].data:
                photo = fhir_patient.photo[0].data
                date = fhir_patient.photo[0].creation
                obj, created = \
                    InsureePhoto.objects.get_or_create(
                        chf_id=imis_insuree.chf_id,
                        defaults={
                            "photo": photo,
                            "date": date,
                            "audit_user_id": -1,
                            "officer_id": 3
                        }
                    )
                imis_insuree.photo_id = obj.id

    @classmethod
    def build_fhir_general_practitioner(cls, fhir_patient, imis_insuree, reference_type):
        from api_fhir_r4.converters import HealthFacilityOrganisationConverter
        if imis_insuree.health_facility:
            hf = HealthFacilityOrganisationConverter.build_fhir_resource_reference(
                imis_insuree.health_facility,
                'Organization',
                reference_type=reference_type
            )
            fhir_patient.generalPractitioner = [hf]

    @classmethod
    def build_imis_general_practitioner(cls, imis_insuree, fhir_patient):
        if not fhir_patient.generalPractitioner:
            return
        if len(fhir_patient.generalPractitioner) != 1:
            # TODO: Check with IG definition. Currently its 0..* but it's not possible to bind more than one HF
            raise FHIRException(_("Patient can provide at most one general practitioner."))

        hf_uuid = cls.get_resource_id_from_reference(fhir_patient.generalPractitioner[0])
        try:
            health_facility = HealthFacility.objects.get(uuid=hf_uuid)
            imis_insuree.health_facility = health_facility
        except HealthFacility.DoesNotExist:
            raise FHIRException(F"Invalid location reference, {hf_uuid} doesn't match any HealthFacility.")

    @classmethod
    def _family_reference_identifier_type(cls, reference_type):
        if reference_type == ReferenceConverterMixin.UUID_REFERENCE_TYPE:
            return cls.build_codeable_concept(R4IdentifierConfig.get_fhir_uuid_type_code())
        elif reference_type == ReferenceConverterMixin.DB_ID_REFERENCE_TYPE:
            return cls.build_codeable_concept(R4IdentifierConfig.get_fhir_id_type_code())
        elif reference_type == ReferenceConverterMixin.CODE_REFERENCE_TYPE:
            # Family don't have code assigned, uuid is used instead
            return cls.build_codeable_concept(R4IdentifierConfig.get_fhir_uuid_type_code())
        pass

    @classmethod
    def _family_reference_identifier_value(cls, family, reference_type):
        if reference_type == ReferenceConverterMixin.UUID_REFERENCE_TYPE:
            return family.uuid
        elif reference_type == ReferenceConverterMixin.DB_ID_REFERENCE_TYPE:
            return family.id
        elif reference_type == ReferenceConverterMixin.CODE_REFERENCE_TYPE:
            # Family don't have code assigned, uuid is used instead
            return family.uuid
        raise NotImplementedError(F"Reference type {reference_type} not implemented for family")

    @classmethod
    def __build_photo_uri(cls, imis_insuree):
        photo_folder = imis_insuree.photo.folder.replace("\\", "/")
        photo_full_path = F"{photo_folder}/{imis_insuree.photo.filename}"
        path = f'/photo/{photo_full_path}'
        return path

    @classmethod
    def _validate_fhir_identifier_is_exist(cls, fhir_patient):
        if not fhir_patient.identifier or len(fhir_patient.identifier) == 0:
            raise FHIRException(
                _('FHIR Patient entity without identifier')
            )

    # fhir validations
    @classmethod
    def _validate_fhir_extension_is_exist(cls, fhir_patient):
        if not fhir_patient.extension or len(fhir_patient.extension) == 0:
            raise FHIRException(
                _('At least one extension with is_head is required')
            )

    @classmethod
    def _validate_imis_is_head(cls, imis_insuree):
        if imis_insuree.head is None:
            raise FHIRException(
                _('Missing is-head in IMIS object')
            )

    @classmethod
    def _validate_fhir_address(cls, fhir_family):
        if not fhir_family.address or len(fhir_family.address) == 0:
            raise FHIRException(
                _('Address must be supported')
            )

    @classmethod
    def _validate_fhir_address_details(cls, addresses):
        addr_errors = {}
        for idx, address in enumerate(addresses):
            errors = []
            # Get last part of each extension url
            if not address.extension:
                raise FHIRException("Missing extensions for Address")

            ext_types = [ext.url.rsplit('/')[-1] for ext in address.extension]
            if 'address-location-reference' not in ext_types:
                errors.append("FHIR Patient address without address-location-reference extension.")
            if 'address-municipality' not in ext_types:
                errors.append("FHIR Patient address without address-municipality reference.")
            if len(ext_types) != 2:
                errors.append("Patient's address should provide exactly 2 extensions")
            if not address.city:
                errors.append("Address 'city' field required")
            if not address.district:
                errors.append("Address 'district' field required")
            if not address.state:
                errors.append("Address 'state' field required")

            if errors:
                addr_errors[idx] = errors

        if addr_errors:
            raise FHIRException(json.dumps(addr_errors))

    @classmethod
    def _validate_fhir_photo(cls, fhir_patient):
        if not fhir_patient.photo or len(fhir_patient.photo) == 0:
            raise FHIRException(
                _('FHIR Patient without photo data.')
            )
        else:
            photo = fhir_patient.photo[0]
            if not photo.title or not photo.creation or not photo.contentType:
                raise FHIRException(
                    _('FHIR Patient misses one of required fields:  contentType, title, creation')
                )

    # imis validations
    @classmethod
    def _validate_imis_identifier_code(cls, imis_insuree):
        if not imis_insuree.chf_id:
            raise FHIRException(
                _('Insuree %(insuree_uuid)s without code') % {'insuree_uuid': imis_insuree.uuid}
            )

    @classmethod
    def _validate_fhir_family_home_slice(cls, fhir_patient):
        is_home_use = False
        for address in fhir_patient.address:
            if address.use == "home":
                is_home_use = True
        if is_home_use == False:
            raise FHIRException(
                _('Patient without family address')
            )

    @classmethod
    def _validate_fhir_patient_human_name(cls, fhir_patient):
        if not fhir_patient.name:
            raise FHIRException(
                _('Missing fhir patient attribute: name')
            )
        for name in fhir_patient.name:
            if not name.family or not name.given:
                raise FHIRException(
                    _('Missing obligatory fields for fhir patient name: family or given')
                )

    @classmethod
    def _validate_imis_insuree_human_name(cls, imis_insuree):
        if not imis_insuree.last_name or not imis_insuree.other_names:
            raise FHIRException(
                _('Missing patient family name or given name')
            )

    @classmethod
    def __add_insuree_current_address(cls, imis_insuree, address):
        imis_insuree.current_address = address.text

    @classmethod
    def __add_insuree_location(cls, imis_insuree, address):
        # Physical address can also provide information regarding current address
        if address.text:
            imis_insuree.current_address = address.text

        for ext in address.extension:
            if "StructureDefinition/address-location-reference" in ext.url:
                location_uuid = LocationConverter.get_resource_id_from_reference(ext.valueReference)
                try:
                    location = Location.objects.get(uuid=location_uuid)
                    imis_insuree.current_village = location
                except Location.DoesNotExist as e:
                    raise FHIRException(f"Invalid location reference, {location_uuid} doesn't match any location.")

    @classmethod
    def __add_insuree_geolocation(cls, imis_insuree, address):
        imis_insuree.geolocation = address.text

    @classmethod
    def _build_insuree_family_address(cls, imis_insuree_family: Family, reference_type):
        return cls.__build_address_of_use(
            address_location=imis_insuree_family.location,
            use='home',
            location_text=imis_insuree_family.address,
            reference_type=reference_type
        )

    @classmethod
    def _build_insuree_address(cls, imis_insuree, reference_type):
        return cls.__build_address_of_use(
            address_location=imis_insuree.current_village,
            use='temp',
            location_text=imis_insuree.current_address,
            reference_type=reference_type
        )

    @classmethod
    def __build_address_of_use(cls, address_location: Location, use: str, location_text: str, reference_type):
        base_address = cls.__build_base_physical_address(address_location, reference_type)
        base_address.use = use
        if location_text:
            base_address.text = location_text
        return base_address

    @classmethod
    def __build_base_physical_address(cls, imis_village_location, reference_type) -> Address:
        return Address(**{
            "type": "physical",
            "state": cls.__state_name_from_physical_location(imis_village_location),
            "district": cls.__district_name_from_physical_location(imis_village_location),
            "city": cls.__village_name_from_physical_location(imis_village_location),
            "extension": [
                cls.__build_municipality_extension(imis_village_location),
                cls.__build_location_reference_extension(imis_village_location, reference_type)
            ]
        })

    @classmethod
    def __build_municipality_extension(cls, insuree_family_location):
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-municipality"
        extension.valueString = cls.__municipality_from_family_location(insuree_family_location)
        return extension

    @classmethod
    def __state_name_from_physical_location(cls, insuree_family_location):
        return insuree_family_location.parent.parent.parent.name

    @classmethod
    def __district_name_from_physical_location(cls, insuree_family_location):
        return insuree_family_location.parent.parent.name

    @classmethod
    def __municipality_from_family_location(cls, insuree_family_location):
        return insuree_family_location.parent.name

    @classmethod
    def __village_name_from_physical_location(cls, insuree_family_location):
        return insuree_family_location.name

    @classmethod
    def __build_location_reference_extension(cls, insuree_family_location, reference_type):
        extension = Extension.construct()
        extension.url = f"{GeneralConfiguration.get_system_base_url()}StructureDefinition/address-location-reference"
        extension.valueReference = LocationConverter \
            .build_fhir_resource_reference(insuree_family_location, 'Location', reference_type=reference_type)
        return extension

    @classmethod
    def __build_imis_family_address(cls, fhir_patient):
        family_address = cls.__get_family_address_from_fhir_patient(fhir_patient)
        return cls.__get_location_from_address(family_address) if family_address else None

    @classmethod
    def __get_location_from_address(cls, fhir_patient_address):
        return LocationConverter.get_location_from_address( LocationConverter, fhir_patient_address)


    @classmethod
    def __get_family_address_from_fhir_patient(cls, fhir_patient) -> Address:
        # Family address is of use home and type physical
        return cls.__get_address_by_properties(fhir_patient, 'home', 'physical')

    @classmethod
    def __get_insuree_current_address_from_fhir_patinet(cls, fhir_patient) -> Address:
        # Family address is of use temp and type physical
        return cls.__get_address_by_properties(fhir_patient, 'temp', 'physical')

    @classmethod
    def __get_address_by_properties(cls, fhir_patient, use=None, type_=None):
        matching = [
            addr for addr in fhir_patient.address
            if use in (addr.use, None) and type_ in (addr.type, None)
        ]
        if len(matching) > 1:
            params = F"type: {type_}," if type_ else ""
            params += F"use: {use}," if use else ""
            raise FHIRException(F"More than one address valid address with ({params})")

        return matching[0] if matching else None

    @classmethod
    def __get_family_from_fhir_patient_extension(cls, fhir_patient):
        if not (family_uuid := cls.__get_family_uuid_from_fhir_patient(fhir_patient)):
            return None

        try:
            return Family.objects.select_related('location').get(uuid=family_uuid)
        except Family.DoesNotExist as e:
            raise FHIRException(F"Invalid location reference, {e} doesn't match any location.")

    @classmethod
    def __get_family_uuid_from_fhir_patient(cls, fhir_patient):
        return next((
            GroupConverter.get_resource_id_from_reference(ext.valueReference)
            for ext in fhir_patient.extension if "/StructureDefinition/patient-group-reference" in ext.url
        ), None)

    @classmethod
    def _is_patient_head(cls, fhir_patient):
        # Get matching extension or return False by default
        extension_gen = (ext.valueBoolean for ext in fhir_patient.extension if 'patient-is-head' in ext.url)
        return next(extension_gen, False)
