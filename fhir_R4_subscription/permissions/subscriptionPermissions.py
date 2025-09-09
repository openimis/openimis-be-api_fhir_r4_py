from ..configurations.R4SubscriptionConfig import R4SubscriptionConfig
from api_fhir_r4.permissions import FHIRApiPermissions


class FHIRApiSubscriptionPermissions(FHIRApiPermissions):
    permissions_get = R4SubscriptionConfig.get_fhir_sub_search_perms()
    permissions_post = R4SubscriptionConfig.get_fhir_sub_create_perms()
    permissions_put = R4SubscriptionConfig.get_fhir_sub_update_perms()
    permissions_patch = R4SubscriptionConfig.get_fhir_sub_update_perms()
    permissions_delete = R4SubscriptionConfig.get_fhir_sub_delete_perms()
