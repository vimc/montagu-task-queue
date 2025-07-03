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

    def __post(self, relative_url, data, headers = None):
        if headers is None:
            headers = self.__default_headers
        response requests.post(self.__url(relative_url, data=data, headers=headers)
        return handle_response(response)

    def __authenticate(self):
        try:
            monty = montagu.MontaguAPI(self.__config.montagu_url, self.__config.montagu_user,
                                               config.montagu_password)
            packit_login_response = self.__get("/auth/login/montagu", {"Authorization": f"Bearer {monty.token}"})
            self.token = packit_login_response.token # TODO: maybe don't need to retain token as saving header?
            self.__default_headers = { "Authorization": f"Bearer {self.token}" }
        except Exception as ex:
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

    def run_packet(self, packet_group, parameters):
        def do_run_packet():
            data = {
                "name": packet_group,
                "parameters": parameters,
                "branch": "",
                "hash": "" # TODO: can branch and hash be empty??
            }
            response = self.__post("/runner/run")
            return response.taskId

        return __self.execute(do_run_packet)

    def poll_running_packet(self, task_id):
        def do_poll_running_packet():
            return self.__get(f"/runner/status/{task_id}")
        return self.__execute(do_poll_running_packet)

    def kill_running_packet(self, task_id):
        def do_kill_running_packet():
            return self.__post(f"/runner/cancel/{task_id}")
        return self.execute(do_kill_running_packet)