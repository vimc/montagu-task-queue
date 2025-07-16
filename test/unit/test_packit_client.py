import json
import montagu
import pytest
import requests_mock
from src.packit_client import PackitClient
from src.packit_client_exception import PackitClientException
from test.unit.test_run_reports import MockConfig, PACKIT_URL
from unittest.mock import patch, MagicMock

config = MockConfig()

def mock_auth(mock_montagu_api_class, requests_mock):
    mock_montagu_api = mock_montagu_api_class.return_value
    mock_montagu_api.token = "test-montagu-token"
    requests_mock.get(f"{PACKIT_URL}/api/auth/login/montagu", text = json.dumps({"token": "test-packit-token"} ))

def assert_expected_packit_api_request(requests_mock, index, method, url, text = None):
    req = requests_mock.request_history[index]
    assert req.headers["Authorization"] == "Bearer test-packit-token"
    assert req.method == method
    assert req.url == url
    assert req.text == text

def assert_expected_packit_auth_request(requests_mock, index):
    auth_req = requests_mock.request_history[index]
    assert auth_req.method == "GET"
    assert auth_req.url == f"{PACKIT_URL}/api/auth/login/montagu"
    assert auth_req.headers["Authorization"] == "Bearer test-montagu-token"


@patch("montagu.MontaguAPI")
def test_authenticates_on_init(MockMontaguAPI, requests_mock):
    mock_auth(MockMontaguAPI, requests_mock)

    sut = PackitClient(config)

    MockMontaguAPI.assert_called_with("http://test-montagu", "test.montagu.user", "montagu_password")
    auth_call = requests_mock.request_history[0]
    assert_expected_packit_auth_request(requests_mock, 0)
    assert sut.auth_success
    assert sut.token == "test-packit-token"


@patch("montagu.MontaguAPI")
def test_refresh_git(MockMontaguAPI, requests_mock):
    mock_auth(MockMontaguAPI, requests_mock)
    requests_mock.post(f"{PACKIT_URL}/api/runner/git/fetch", text = None)

    sut = PackitClient(config)
    sut.refresh_git()

    assert_expected_packit_api_request(requests_mock, 1, "POST", f"{PACKIT_URL}/api/runner/git/fetch")

@patch("montagu.MontaguAPI")
def test_run(MockMontaguAPI, requests_mock):
    mock_auth(MockMontaguAPI, requests_mock)
    mock_branches_response = { "branches": [
        { "name": "some_other_branch", "commitHash": "xyz987" },
        { "name": "main", "commitHash": "abc123" }
    ] }
    requests_mock.get(f"{PACKIT_URL}/api/runner/git/branches", text = json.dumps(mock_branches_response))
    requests_mock.post(f"{PACKIT_URL}/api/runner/run", text = json.dumps({ "taskId": "test-task-id" }))

    sut = PackitClient(config)
    task_id = sut.run("test-packet-group", {"a": 1, "b": 2})

    assert task_id == "test-task-id"
    assert_expected_packit_api_request(requests_mock, 1, "GET", f"{PACKIT_URL}/api/runner/git/branches")
    expected_run_payload = json.dumps({
        "name": "test-packet-group",
        "parameters": {"a": 1, "b": 2},
        "branch": "main",
        "hash": "abc123"
    })
    assert_expected_packit_api_request(requests_mock, 2, "POST", f"{PACKIT_URL}/api/runner/run", expected_run_payload)


@patch("montagu.MontaguAPI")
def test_poll_status(MockMontaguAPI, requests_mock):
    mock_auth(MockMontaguAPI, requests_mock)
    mock_poll_response = { "status": "RUNNING" }
    requests_mock.get(f"{PACKIT_URL}/api/runner/status/test-task-id", text = json.dumps(mock_poll_response))

    sut = PackitClient(config)
    resp = sut.poll("test-task-id")

    assert resp == mock_poll_response

@patch("montagu.MontaguAPI")
def test_kill_task(MockMontaguAPI, requests_mock):
    mock_auth(MockMontaguAPI, requests_mock)
    mock_kill_response = { "status": "dead" }
    requests_mock.post(f"{PACKIT_URL}/api/runner/cancel/test-task-id", text = json.dumps(mock_kill_response))

    sut = PackitClient(config)
    resp = sut.kill_task("test-task-id")

    assert resp == mock_kill_response
    assert_expected_packit_api_request(requests_mock, 1, "POST", f"{PACKIT_URL}/api/runner/cancel/test-task-id")


@patch("montagu.MontaguAPI")
def test_publish(MockMontaguAPI, requests_mock):
    mock_auth(MockMontaguAPI, requests_mock)
    # publish polls for the packit - return 404 on first poll, 200 on second poll
    requests_mock.get(f"{PACKIT_URL}/api/packets/test-packet-id", [
        { "text": json.dumps({ "error": { "detail": "not found" } }),  "status_code": 404},
        { "text": json.dumps({ "id": "test-packet-id", "name": "A packet" }), "status_code": 200 }
    ])
    expected_permissions_payload = json.dumps({
        "addPermissions": [{ "permission": "packet.read", "packetId": "test-packet-id" }],
        "removePermissions": []
    })
    requests_mock.put(f"{PACKIT_URL}/api/roles/test-role-1/permissions", json = "null")
    requests_mock.put(f"{PACKIT_URL}/api/roles/test-role-2/permissions", text = "null")

    sut = PackitClient(config)
    result = sut.publish("A packet", "test-packet-id", ["test-role-1", "test-role-2"])
    assert_expected_packit_api_request(requests_mock, 1, "GET", f"{PACKIT_URL}/api/packets/test-packet-id", None)
    assert_expected_packit_api_request(requests_mock, 2, "GET", f"{PACKIT_URL}/api/packets/test-packet-id", None)

    assert_expected_packit_api_request(requests_mock, 3, "PUT", f"{PACKIT_URL}/api/roles/test-role-1/permissions", expected_permissions_payload)
    assert_expected_packit_api_request(requests_mock, 4, "PUT", f"{PACKIT_URL}/api/roles/test-role-2/permissions", expected_permissions_payload)
    assert result

@patch("montagu.MontaguAPI")
def test_sets_auth_success_to_false_when_auth_fails(MockMontaguAPI, requests_mock):
    requests_mock.get(f"{PACKIT_URL}/api/auth/login/montagu", status_code = 401, text = json.dumps({"error": "Unauthorized"}))
    sut = PackitClient(config)
    assert not sut.auth_success

@patch("montagu.MontaguAPI")
def test_reauthenticates_on_401(MockMontaguAPI, requests_mock):
    # Reauthentication should take place as part of the __execute wrapper used
    # with all methods which require authentication - here we just test a sample
    # method to check the pattern works.
    mock_auth(MockMontaguAPI, requests_mock)
    mock_successful_kill_response = { "status": "dead" }
    requests_mock.post(f"{PACKIT_URL}/api/runner/cancel/test-task-id", [
        {"status_code": 401, "text": json.dumps({"error": "Unauthorized"})},
        {"status_code": 200, "text": json.dumps(mock_successful_kill_response)}
    ])

    sut = PackitClient(config)
    resp = sut.kill_task("test-task-id")

    assert resp == mock_successful_kill_response

    assert_expected_packit_api_request(requests_mock, 1, "POST", f"{PACKIT_URL}/api/runner/cancel/test-task-id")
    assert_expected_packit_auth_request(requests_mock, 2)
    assert_expected_packit_api_request(requests_mock, 3, "POST", f"{PACKIT_URL}/api/runner/cancel/test-task-id")

@patch("montagu.MontaguAPI")
def test_raises_exception_on_unexpected_status(MockMontaguAPI, requests_mock):
    mock_auth(MockMontaguAPI, requests_mock)
    # execute does not tolerate status codes other than 401 - should get an exception
    bad_response = {"error": "Bad request"}
    requests_mock.get(f"{PACKIT_URL}/api/runner/status/test-task-id", status_code = 400, text = json.dumps(bad_response))

    sut = PackitClient(config)
    with pytest.raises(PackitClientException) as exc_info:
        sut.poll("test-task-id")
    assert exc_info.value.response.status_code == 400
    assert exc_info.value.response.json() == bad_response



