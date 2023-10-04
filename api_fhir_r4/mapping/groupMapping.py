from insuree.models import FamilyType, ConfirmationType


class GroupTypeMapping(object):

    group_type = {}
    @classmethod
    def load(cls):
        cls.group_type = {
            str(family_type.code): family_type.type for family_type in FamilyType.objects.all()
        }


class ConfirmationTypeMapping(object):

    confirmation_type = {}
    @classmethod
    def load(cls):
        cls.confirmation_type = {
            str(confirmation_type.code): confirmation_type.confirmationtype for confirmation_type in ConfirmationType.objects.all()
        }
