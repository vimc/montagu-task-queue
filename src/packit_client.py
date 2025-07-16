import json
import logging
import requests
import montagu
import time
from .packit_client_exception import PackitClientException


class PackitClient:
    def __init__(self, config):
        self.__config = config
        self.__verify = not config.packit_disable_certificate_verify
        self.__authenticate()

    def __url(self, relative_url):
        return f"{self.__config.packit_url}/api{relative_url}"

    @staticmethod
    def handle_response(response):
        if response.status_code != 200 and response.status_code != 204:
            raise PackitClientException(response)
        return response.json() if len(response.text) > 0 else None

    @staticmethod
    def serialize(data):
        return None if data is None else json.dumps(data)

    def __get(self, relative_url, headers=None):
        if headers is None:
            headers = self.__default_headers
        response = requests.get(self.__url(relative_url),
                                headers=headers,
                                verify=self.__verify)
        return PackitClient.handle_response(response)

    def __post(self, relative_url, data):
        response = requests.post(self.__url(relative_url),
                                 data=PackitClient.serialize(data),
                                 headers=self.__default_headers,
                                 verify=self.__verify)
        return PackitClient.handle_response(response)

    def __put(self, relative_url, data):
        response = requests.put(self.__url(relative_url),
                                data=PackitClient.serialize(data),
                                headers=self.__default_headers,
                                verify=self.__verify)
        return PackitClient.handle_response(response)

    def __authenticate(self):
        try:
            monty = montagu.MontaguAPI(self.__config.montagu_url,
                                       self.__config.montagu_user,
                                       self.__config.montagu_password)
            packit_login_response = self.__get(
                "/auth/login/montagu",
                {"Authorization": f"Bearer {monty.token}"})
            self.auth_success = True
            self.token = packit_login_response["token"]
            self.__default_headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": f"application/json"
            }
        except Exception as ex:
            self.auth_success = False
            logging.exception(ex)

    def __execute(self, func, *args):  # TODO: maybe don't need args?
        # retry an operation if it fails auth (probably because of an expired
        # packit token)
        try:
            return func(*args)
        except PackitClientException as ex:
            if ex.response.status_code == 401:
                self.__authenticate()
                return func(*args)
            else:
                raise ex

    def __get_latest_commit_for_branch(self, branch):
        branches_response = self.__get("/runner/git/branches")
        branches = branches_response["branches"]
        branch_details = next(
            filter(lambda b: b["name"] == branch, branches), None)
        if branch_details is None:
            raise Exception(f"Git details not found for branch {branch}")
        return branch_details["commitHash"]

    def __wait_for_packet_to_be_imported(self, packet_id):
        # packet api imports new packets every 10s - poll it for a generous
        # 30s to find a new packet before attempting to publish it
        poll_seconds = 2
        seconds_max = 30
        poll_max = seconds_max / poll_seconds
        poll_counter = 0
        while poll_counter <= poll_max:
            try:
                self.__get(f"/packets/{packet_id}")
                return
            except PackitClientException as ex:
                logging.info(f"Waiting for packet {packet_id}...")
            poll_counter = poll_counter + 1
            time.sleep(poll_seconds)
        raise Exception(
            f"Packet {packet_id} was not imported into Packit after " +
            f"{seconds_max}s")

    def refresh_git(self):
        def do_refresh_git():
            self.__post("/runner/git/fetch", None)
        self.__execute(do_refresh_git)

    def run(self, packet_group, parameters):
        def do_run():
            branch = "main"
            commit = self.__get_latest_commit_for_branch(branch)
            data = {
                "name": packet_group,
                "parameters": parameters,
                "branch": branch,
                "hash": commit
            }
            response = self.__post("/runner/run", data)
            return response["taskId"]

        return self.__execute(do_run)

    def poll(self, task_id):
        def do_poll():
            return self.__get(f"/runner/status/{task_id}")
        return self.__execute(do_poll)

    def kill_task(self, task_id):
        def do_kill_task():
            return self.__post(f"/runner/cancel/{task_id}", None)
        return self.__execute(do_kill_task)

    def publish(self, name, packet_id, roles):
        # mimic OW publishing by setting packet-level permission for a new
        # report packet permission on a list of configured roles.
        # NB: These role can either be user # roles or groups.
        # If users, these need to be user names not email  addresses.
        def do_publish_to_role(role):
            data = {
                "addPermissions": [{
                    "permission": "packet.read",
                    "packetId": packet_id
                }],
                "removePermissions": []
            }
            self.__put(f"/roles/{role}/permissions", data)

        self.__execute(
            lambda: self.__wait_for_packet_to_be_imported(packet_id))

        logging.info(f"Publishing packet {name}({packet_id})")
        success = True
        for role in roles:
            try:
                logging.info(f"...to role {role}")
                self.__execute(lambda: do_publish_to_role(role))
            except Exception as ex:
                logging.exception(ex)
                success = False
        return success
