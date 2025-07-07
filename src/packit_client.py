import logging
import requests
import montagu
from .packit_client_exception import PackitClientException

class PackitClient:
    def __init__(self, config):
        self.__config = config
        self.__authenticate()

    def __url(self, relative_url):
        # TODO: add base url to config
        return f"{self.__config.packit_api_url}{relative_url}"

    @staticmethod
    def handle_response(response):
        if response.status_code != 200 and response.status_code != 204:
            raise PackitClientException(response)
        return response.json()

    def __get(self, relative_url, headers = None):
        if headers is None:
            headers = self.__default_headers
        response = requests.get(self.__url(relative_url), headers=headers)
        return handle_response(response)

    def __post(self, relative_url, data):
        response = requests.post(self.__url(relative_url, data=data, headers=self.__default_headers)
        return handle_response(response)

    def __put(self, relative_url, data):
        response = requests.put(self.__url(relative_url, datadata, headers=self.__default_headers)
        return handle_response(response)

    def __authenticate(self):
        try:
            monty = montagu.MontaguAPI(self.__config.montagu_url, self.__config.montagu_user,
                                               config.montagu_password)
            packit_login_response = self.__get("/auth/login/montagu", {"Authorization": f"Bearer {monty.token}"})
            self.auth_success = True
            self.token = packit_login_response.token # TODO: maybe don't need to retain token as saving header?
            self.__default_headers = { "Authorization": f"Bearer {self.token}" }
        except Exception as ex:
            self.auth_success = False
            logging.exception(ex)

    def __execute(self, func, *args): # TODO: maybe don't need args?
            # retry an operation if it fails auth (probably because of an expired packit token)
            try:
                return func(*args)
            except PackitClientException as ex:
                if ex.response.status_code == 401:
                    self.__authenticate()
                    return func(*args)
                else:
                    raise ex

    def run(self, packet_group, parameters):
        def do_run():
            data = {
                "name": packet_group,
                "parameters": parameters,
                "branch": "",
                "hash": "" # TODO: can branch and hash be empty??
            }
            response = self.__post("/runner/run", data)
            return response.taskId

        return self.__execute(do_run)

    def poll(self, task_id):
        def do_poll():
            return self.__get(f"/runner/status/{task_id}")
        return self.__execute(do_poll)

    def kill_task(self, task_id):
        def do_kill_task():
            return self.__post(f"/runner/cancel/{task_id}", None)
        return self.__execute(do_kill_task)

   def publish(self, packet_id, roles):
       # mimic OW publishing by setting packet-level permission for a new report packet permission
       # on a list of configured roles. NB: These role can either be user roles or groups. If users,
       # these need to be user names not email addresses.
       def do_publish_to_role(role):
           data = {
            "addPermissions": [
                "permission": "packit.read",
                "packetId": packet_id
            ],
            "removePermissions": []
           }
           self.__put(f"/roles/{role}/permissions", data)

       logging.info(f"Publishing packet {name}({packet_id})")
       success = True
       for role in roles:
           try
             logging.info(f"...to role {role}")
             self.__execute(do_publish_to_role(role))
           except Exception as ex:
               logging.exception(ex)
               success = False
       return success
