from api_fhir_r4.utils import DbManagerUtils
from core.forms import User
from core.services import create_or_update_interactive_user, create_or_update_core_user
import json
import os


class LogInMixin:
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
    

    def load_user_data_from_json(self, json_path):
        """
        Purpose: one
        """
        dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        json_representation = json.loads(open(dir_path + json_path).read())
        if 'username' in json_representation and 'password' in json_representation:
            self._test_username = json_representation['username']
            self._test_username = json_representation['password']
        else:
            raise Exception("Json not containing credentials")
    # end def

    def get_or_create_user_api(self):
        user = DbManagerUtils.get_object_or_none(User, username=self._TEST_USER_NAME)
        if user is None:
            user = self.__create_user_interactive_core()
        user.set_password(self._TEST_USER_PASSWORD)
        user.save()
        return user

    def __create_user_interactive_core(self):
        i_user, i_user_created = create_or_update_interactive_user(
            user_id=None, data=self._TEST_DATA_USER, audit_user_id=999, connected=False)
        create_or_update_core_user(
            user_uuid=None, username=self._TEST_DATA_USER["username"], i_user=i_user)
        return DbManagerUtils.get_object_or_none(User, username=self._TEST_USER_NAME)
