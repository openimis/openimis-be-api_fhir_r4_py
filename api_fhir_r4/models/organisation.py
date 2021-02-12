from api_fhir_r4.models import BackboneElement, DomainResource, Property,Element

class OrganisationContact(Element):
    address = Property('address', 'Address', count_max='*')
    name = Property('name', 'HumanName', count_max='*')
    telecom = Property('telecom','ContactPoint', count_max='*')
 
class Organisation(DomainResource):
    identifier = Property('identifier', 'Identifier', count_max='*')
    active = Property('active', bool)
    address = Property('address', 'Address', count_max='*')
    location = Property('location', 'Location', count_max='*')
    code = Property('code',str)
    name = Property('name',str)
    phone = Property('phone',str)
    fax = Property('fax',str)
    email = Property('email',str)
    date_created = Property('date_created', 'FHIRDate')
    contact = Property('contact','OrganisationContact', count_max='*')
    legal_form = Property('legal_form',str)
    activity_code = Property('activity_code',str)
    accountancy_account = Property('accountancy_account',str)
    bank_account =Property('bank_account', 'BankAccount')
    payment_reference = Property('payment_reference',str)