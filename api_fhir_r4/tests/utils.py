import os
import json
from core.models import User
from api_fhir_r4.utils import DbManagerUtils
from core.services import create_or_update_interactive_user, create_or_update_core_user

def load_and_replace_json(path=None,sub_str={}):
    test_root = os.path.dirname(os.path.realpath(__file__))
    #removing the leading / of path
    path = path[1:] if path[0] == '/' else path
    json_representation = open(os.path.join(test_root,path)).read()

    for s_str in sub_str:
        json_representation = json_representation.replace(str(s_str),str(sub_str[s_str]))   
    
    return json.loads(json_representation)

# example of use
#        self.sub_str[self._TEST_VILLAGE_UUID] = self.test_village.uuid
#        self.sub_str[self._TEST_SUBSTITUTION_OFFICER_UUID] = self.test_officer.uuid
#        self.sub_str[self._TEST_GROUP_UUID] = self.test_insuree.family.uuid
#        self.sub_str[self._TEST_INSUREE_UUID] = self.test_insuree.uuid
#        self.sub_str[self._TEST_INSUREE_CHFID] = self.test_insuree.chf_id
#        self.sub_str[self._TEST_OFFICER_UUID] = self.test_officer.uuid
#        self.sub_str[self._TEST_CLAIM_ADMIN_UUID] = self.test_claim_admin.uuid
#        self.sub_str[self._TEST_PRODUCT_UUID] = self.test_product.uuid
#       
#        self.sub_str[self._TEST_HF_UUID] = self.test_hf.uuid
#        
#        self.json_representation = load_and_replace_json(_test_json_request_path,self.sub_str)
_TEST_USER_NAME = "TestUserTest2"
_TEST_USER_PASSWORD = "TestPasswordTest2"
_TEST_DATA_USER = {
    "username": _TEST_USER_NAME,
    "last_name": _TEST_USER_NAME,
    "password": _TEST_USER_PASSWORD,
    "other_names": _TEST_USER_NAME,
    "user_types": "INTERACTIVE",
    "language": "en",
    "roles": [1, 3, 5, 9],
}

def get_connection_payload(userdata=_TEST_DATA_USER):
    return {
        "username": userdata['username'],
        "password": userdata['password']
    }


def get_or_create_user_api(userdata=_TEST_DATA_USER):
    user = DbManagerUtils.get_object_or_none(User, username=userdata['username'])
    if user is None:
        user = __create_user_interactive_core(userdata)
    user.set_password(userdata['password'])
    user.save()
    return user

def __create_user_interactive_core(userdata):
    i_user, i_user_created = create_or_update_interactive_user(
        user_id=None, data=userdata, audit_user_id=999, connected=False
    )
    create_or_update_core_user(
        user_uuid=None, username=userdata['username'], i_user=i_user
    )
    return DbManagerUtils.get_object_or_none(User, username=userdata['username'])