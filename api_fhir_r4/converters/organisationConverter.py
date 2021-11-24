from django.utils.translation import gettext
from policyholder.models import PolicyHolder
from location.models import Location
from api_fhir_r4.configurations import R4IdentifierConfig, GeneralConfiguration
from api_fhir_r4.converters import BaseFHIRConverter,ReferenceConverterMixin
from api_fhir_r4.converters.healthcareServiceConverter import HealthcareServiceConverter
from api_fhir_r4.converters.locationConverter import LocationConverter
from fhir.resources.extension import Extension
from fhir.resources.attachment import Attachment
from fhir.resources.coding import Coding
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.organization import Organization, OrganizationContact
from api_fhir_r4.utils import TimeUtils, DbManagerUtils


class OrganisationConverter(BaseFHIRConverter):
    
    @classmethod
    def to_fhir_obj(cls, imis_organisation, reference_type=ReferenceConverterMixin.UUID_REFERENCE_TYPE):
        # TODO reshape this fhir object and imis, fix BankAccount
        fhir_organisation = Organization()
        cls.build_fhir_pk(fhir_organisation, imis_organisation.id)
        # TODO - locaction - as an extension?
        #cls.build_fhir_location(fhir_organisation, imis_organisation)
        cls.build_fhir_name(fhir_organisation, imis_organisation)
        # TODO - fix contact name field
        #cls.build_fhir_contact_name(imis_organisation, fhir_organisation)
        cls.build_fhir_date(fhir_organisation, imis_organisation)
        cls.build_fhir_legal_form(fhir_organisation, imis_organisation)
        cls.build_fhir_phone(fhir_organisation, imis_organisation)
        cls.build_fhir_fax(fhir_organisation, imis_organisation)
        cls.build_fhir_email(fhir_organisation, imis_organisation)
        cls.build_fhir_code(fhir_organisation, imis_organisation)
        cls.build_fhir_addresses(fhir_organisation, imis_organisation)
        cls.build_fhir_accountancy_account(fhir_organisation, imis_organisation)
        #cls.build_fhir_bank_account(fhir_organisation,imis_organisation)
        return fhir_organisation

    @classmethod
    def to_imis_obj(cls, fhir_organisation, audit_user_id):
        errors = []
        fhir_organisation = Organization(**fhir_organisation)
        imis_organisation = PolicyHolder()
        imis_organisation.date_created = TimeUtils.now()
        imis_organisation.date_updated = TimeUtils.now()
        cls.build_imis_addresses(imis_organisation,fhir_organisation)
        cls.build_imis_identifiers(imis_organisation,fhir_organisation)
        cls.build_imis_name(imis_organisation,fhir_organisation)
        cls.build_imis_code(imis_organisation,fhir_organisation,errors)
        cls.build_imis_phone(imis_organisation,fhir_organisation,errors)
        cls.build_imis_email(imis_organisation,fhir_organisation)
        cls.build_imis_contact(imis_organisation,fhir_organisation)
        cls.build_imis_fax(imis_organisation,fhir_organisation)
        cls.build_imis_bank_account(imis_organisation,fhir_organisation)
        cls.build_imis_accountancy_account(imis_organisation,fhir_organisation)
        cls.build_imis_legal_form(imis_organisation,fhir_organisation,errors)
        cls.check_errors(errors)
        return imis_organisation

    @classmethod
    def build_imis_addresses(cls,imis_organisation,fhir_organisation):
        addresses = fhir_organisation.address
        address={}
        if addresses is not None:
            address['text']=addresses[0].text
            address['type']=addresses[0].type
            address['use']=addresses[0].use
        imis_organisation.address=address

    @classmethod
    def get_reference_obj_id(cls, imis_organisation):
        return imis_organisation.uuid

    @classmethod
    def get_fhir_resource_type(cls):
        return Organization

    @classmethod
    def get_imis_obj_by_fhir_reference(cls, reference, errors=None):
        imis_organisation_uuid = cls.get_resource_id_from_reference(reference)
        return DbManagerUtils.get_object_or_none(Insuree, uuid=imis_organisation_uuid)

    @classmethod
    def build_imis_code(cls,imis_organisation,fhir_organisation,errors):
        code =fhir_organisation.code
        if not cls.valid_condition(code is None,gettext('Missing  `code` attribute'), errors):
            imis_organisation.code=fhir_organisation.code
         
    @classmethod
    def build_imis_phone(cls,imis_organisation,fhir_organisation,errors):
        phone=fhir_organisation.phone
        if not cls.valid_condition(phone is None,gettext('Missing  `phone` attribute'), errors):
            imis_organisation.phone=fhir_organisation.phone
            
    @classmethod
    def build_imis_legal_form(cls,imis_organisation,fhir_organisation,errors):
        legal_form=fhir_organisation.legal_form
        if not cls.valid_condition(legal_form is None,gettext('Missing  `legal_form` attribute'), errors):
            imis_organisation.legal_form = fhir_organisation.legal_form
    
    @classmethod
    def build_imis_fax(cls,imis_organisation,fhir_organisation):
        imis_organisation.fax = fhir_organisation.fax 
    
    @classmethod
    def build_imis_bank_account(cls,imis_organisation,fhir_organisation):
        bank = cls.build_bank(fhir_organisation.bank_account)
        imis_organisation.bank_account = bank
    
    @classmethod
    def build_imis_accountancy_account(cls,imis_organisation,fhir_organisation):
        if fhir_organisation.accountancy_account:
        #    print(fhir_organisation.accountancy_account)
           imis_organisation.accountancy_account = fhir_organisation.accountancy_account
    
    @classmethod
    def build_imis_contact(cls,imis_organisation,fhir_organisation):
        if fhir_organisation.contact:
            imis_organisation.contact_name = fhir_organisation.contact[0]
        
    @classmethod
    def build_imis_email(cls,imis_organisation,fhir_organisation):
        imis_organisation.email=fhir_organisation.email 
      
    @classmethod
    def build_fhir_name(cls,fhir_organisation, imis_organisation):
        name = imis_organisation.trade_name
        fhir_organisation.name = name
        
        
        
    @classmethod
    def build_imis_name(cls,imis_organisation,fhir_organisation):
        imis_organisation.trade_name = fhir_organisation.name
         
    @classmethod
    def build_fhir_phone(cls,fhir_organisation, imis_organisation):
        phone = imis_organisation.phone
        fhir_organisation.phone = phone
        
    @classmethod
    def build_fhir_legal_form(cls,fhir_organisation, imis_organisation):
        fhir_organisation.legal_form = imis_organisation.legal_form
    @classmethod
    def build_fhir_date(cls,fhir_organisation, imis_organisation):
        fhir_organisation.date_created = imis_organisation.date_created.isoformat()
        
    @classmethod
    def build_fhir_phone(cls,fhir_organisation, imis_organisation):
        phone = imis_organisation.phone
        fhir_organisation.phone = phone
    
    @classmethod
    def build_fhir_email(cls,fhir_organisation, imis_organisation):
        email = imis_organisation.email
        fhir_organisation.email = email
        
    @classmethod
    def build_fhir_code(cls,fhir_organisation, imis_organisation):
        code = imis_organisation.code
        fhir_organisation.code = code
    
    @classmethod
    def build_fhir_accountancy_account(cls,fhir_organisation, imis_organisation):
        if imis_organisation.accountancy_account:
           fhir_organisation.accountancy_account = imis_organisation.accountancy_account
    @classmethod
    def build_fhir_bank_account(cls,fhir_organisation, imis_organisation):
        if imis_organisation.bank_account:
           fhir_organisation.bank_account = imis_organisation.bank_account
    @classmethod
    def build_fhir_fax(cls,fhir_organisation, imis_organisation):
        fax = imis_organisation.fax
        fhir_organisation.fax = fax
        
    @classmethod
    def build_fhir_identifiers(cls, fhir_organisation, imis_organisation):
        identifiers = []
        cls.build_fhir_uuid_identifier(identifiers, imis_organisation)
        fhir_organisation.identifier = identifiers

    @classmethod
    def build_imis_identifiers(cls, imis_organisation, fhir_organisation):
        value = cls.get_fhir_identifier_by_code(fhir_organisation.identifier,
                                                R4IdentifierConfig.get_fhir_uuid_type_code())
        # if value:
        #     imis_organisation.id= value
     
    @classmethod
    def build_fhir_location(cls, fhir_organisation, imis_organisation):
        locations = []
        if imis_organisation.locations is not None:
            locations.append({"name": imis_organisation.locations.name})
        if type(fhir_organisation.location) is not list:
            fhir_organisation.location = locations
        else:
            fhir_organisation.location.append(locations)
    

    @classmethod
    def build_fhir_telecom(cls, fhir_organisation, imis_organisation):
        fhir_organisation.telecom = cls.build_fhir_telecom_for_person(phone=imis_organisation.phone, email=imis_organisation.email)

    @classmethod
    def build_imis_contacts(cls, imis_organisation, fhir_organisation):
        imis_organisation.phone, imis_organisation.email = cls.build_imis_phone_num_and_email(fhir_organisation.telecom)

    @classmethod
    def build_fhir_addresses(cls, fhir_organisation, imis_organisation):
        addresses = []
        if imis_organisation.address is not None:
            addresses.append(imis_organisation.address)
        if type(fhir_organisation.address) is not list:
            fhir_organisation.address = addresses
        else:
            fhir_organisation.address.append(addresses)


    @classmethod
    def build_fhir_contact_name(cls,imis_organisation,fhir_organisation):
        contacts =[]
        #contact = ContactPoint()
        if imis_organisation.contact_name is not None:
            # contact.system = imis_organisation.contact_name['system']
            contacts.append(imis_organisation.contact_name)
        if type(fhir_organisation.contact) is not list:
            fhir_organisation.contact = contacts
        else:
            fhir_organisation.contact.append(contacts)
        