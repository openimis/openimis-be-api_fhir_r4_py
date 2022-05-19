from django.utils.translation import gettext

from api_fhir_r4.converters import BaseFHIRConverter
from api_fhir_r4.exceptions import FHIRRequestProcessException
from fhir.resources.humanname import HumanName

from api_fhir_r4.models.imisModelEnums import ContactPointSystem, ContactPointUse


class PersonConverterMixin(object):

    @classmethod
    def build_fhir_names_for_person(cls, person_obj):
        if not hasattr(person_obj, 'last_name') and not hasattr(person_obj, 'other_names'):
            raise FHIRRequestProcessException([gettext('Missing `last_name` and `other_names` for IMIS object')])
        name = HumanName.construct()
        name.use = "usual"
        name.family = person_obj.last_name
        name.given = [person_obj.other_names]
        return name

    @classmethod
    def build_imis_last_and_other_name(cls, names):
        last_name = None
        other_names = None
        if isinstance(names, list):
            for name in names:
                if name.use == "usual":
                    last_name = name.family
                    given_names = name.given
                    if given_names and len(given_names) > 0:
                        other_names = given_names[0]
                    break
        return last_name, other_names

    @classmethod
    def build_fhir_telecom_for_person(cls, phone=None, email=None):
        telecom = []
        if phone:
            phone = BaseFHIRConverter.build_fhir_contact_point(phone, ContactPointSystem.PHONE, ContactPointUse.HOME)
            telecom.append(phone)
        if email:
            email = BaseFHIRConverter.build_fhir_contact_point(email, ContactPointSystem.EMAIL, ContactPointUse.HOME)
            telecom.append(email)
        return telecom

    @classmethod
    def build_imis_phone_num_and_email(cls, telecom):
        phone = None
        email = None
        if telecom is not None:
            for contact_point in telecom:
                if contact_point.system == ContactPointSystem.PHONE.value:
                    phone = contact_point.value
                elif contact_point.system == ContactPointSystem.EMAIL.value:
                    email = contact_point.value
        return phone, email
