from insuree.models import Profession, Education, IdentificationType, Relation, Gender

from api_fhir_r4.configurations import GeneralConfiguration


class RelationshipMapping(object):
    relationship = {}
    @classmethod
    def load(cls):
        if cls.relationship == {}:
            cls.relationship = {
                str(relation.id): relation.relation for relation in Relation.objects.all()
            }


class EducationLevelMapping(object):
    education_level = {}
    
    @classmethod
    def load(cls):
        if cls.education_level ==  {}:
            cls.education_level = {
                str(education.id): education.education for education in Education.objects.all()
                }


class PatientProfessionMapping(object):
    patient_profession = {}
    @classmethod
    def load(cls):
        if cls.patient_profession ==  {}:
            cls.patient_profession = {
                str(profession.id): profession.profession for profession in Profession.objects.all()
            }


class IdentificationTypeMapping(object):
    identification_type = {}
    @classmethod
    def load(cls):
        if cls.identification_type == {}:
            cls.identification_type = {
                identification.code: identification.identification_type for identification in IdentificationType.objects.all()
            }


class MaritalStatusMapping(object):
    marital_status = {
        "M": "Married",
        "S": "Single",
        "D": "Divorced",
        "W": "Widowed",
        "UNK": "unknown"
    }


class PatientCategoryMapping(object):
    GENDER_SYSTEM = "http://hl7.org/fhir/administrative-gender"
    AGE_SYSTEM = f"{GeneralConfiguration.get_system_base_url()}CodeSystem/usage-context-age-type"
    imis_gender_mapping = {}
    fhir_patient_category_coding = {
        "male": {
            "system": GENDER_SYSTEM,
            "code": "male",
            "display": "Male",
        },
        "female": {
            "system": GENDER_SYSTEM,
            "code": "female",
            "display": "Female",
        },
        "adult": {
            "system": AGE_SYSTEM,
            "code": "adult",
            "display": "Adult",
        },
        "child": {
            "system": AGE_SYSTEM,
            "code": "child",
            "display": "Child",
        },
    }
    @classmethod
    def get_genders(cls):
        imis_gender_mapping = {
            # FHIR Gender code to IMIS object
            'male': Gender.objects.get(pk='M'),
            'female': Gender.objects.get(pk='F'),
        }

        o = Gender.objects.filter(pk='O').first()
        if o:
            imis_gender_mapping['other'] = o
        return imis_gender_mapping
    @classmethod
    def load(cls):
        if cls.imis_gender_mapping ==  {}:
            cls.imis_gender_mapping = cls.get_genders()

    imis_patient_category_flags = {
        "male": 1,
        "female": 2,
        "adult": 4,
        "child": 8,
    }
