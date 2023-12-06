from enum import Enum
from functools import lru_cache


class ImisMaritalStatus(Enum):
    MARRIED = "M"
    SINGLE = "S"
    DIVORCED = "D"
    WIDOWED = "W"
    NOT_SPECIFIED = "N"


class ImisHfLevel(Enum):
    HEALTH_CENTER = "C"
    HOSPITAL = "H"
    DISPENSARY = "D"


class ImisLocationType(Enum):
    REGION = "R"
    DISTRICT = "D"
    WARD = "W"
    VILLAGE = "V"


class ImisClaimIcdTypes(Enum):
    ICD_0 = "icd_0"
    ICD_1 = "icd_1"
    ICD_2 = "icd_2"
    ICD_3 = "icd_3"
    ICD_4 = "icd_4"


class ImisCategoryDefinition(Enum):
    CATEGORY_SURGERY = "Surgery"
    CATEGORY_DELIVERY = "Delivery"
    CATEGORY_ANTENATAL = "Antenatal"
    CATEGORY_HOSPITALIZATION = "Hospitalization"
    CATEGORY_CONSULTATION = "Consultation"
    CATEGORY_OTHER = "Other"
    CATEGORY_VISIT = "Visit"

    @classmethod
    def get_category_display(cls, category_char):
        @lru_cache(maxsize=1)
        def cached_categories():
            return {
                "S": cls.CATEGORY_SURGERY.value,
                "D": cls.CATEGORY_DELIVERY.value,
                "A": cls.CATEGORY_ANTENATAL.value,
                "H": cls.CATEGORY_HOSPITALIZATION.value,
                "C": cls.CATEGORY_CONSULTATION.value,
                "O": cls.CATEGORY_OTHER.value,
                "V": cls.CATEGORY_VISIT.value,
            }
        try:
            cached_categories()[category_char]
        except KeyError as e:
            raise ValueError(
                f"Invalid category code: {category_char}, available categories are: \n{cached_categories()}"
            )


class BundleType(Enum):
    """
    fhir.resources.R4B doesn't use enum for bundle type,
    see https://github.com/nazrulworld/fhir.resources.R4B/blob/91bf2064aa03c6f3c252d26d7945fa0bb140b03a/fhir/resources/bundle.py#L103
    this class allows to use constants instead of plain strings.
    """
    DOCUMENT = "document"
    MESSAGE = "message"
    TRANSACTION = "transaction"
    TRANSACTION_RESPONSE = "transaction-response"
    BATCH = "batch"
    BATCH_RESPONSE = "batch-response"
    HISTORY = "history"
    SEARCHSET = "searchset"
    COLLECTION = "collection"


class ContactPointSystem(Enum):
    PHONE = "phone"
    FAX = "fax"
    EMAIL = "email"
    PAGER = "pager"
    URL = "url"
    SMS = "sms"
    OTHER = "other"


class ContactPointUse(Enum):
    HOME = "home"
    WORK = "work"
    TEMP = "temp"
    OLD = "old"
    MOBILE = "mobile"


class AddressType(Enum):
    POSTAL = "postal"
    PHYSICAL = "physical"
    BOTH = "both"
