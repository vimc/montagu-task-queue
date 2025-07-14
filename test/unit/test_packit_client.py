import json
import montagu
import requests_mock
from src.packit_client import PackitClient
from unittest.mock import patch, MagicMock

PACKIT_URL = "http://test-packit"

class MockConfig:
    def __init__(self):
        self.disable_certificate_verify = False
        self.montagu_url = "http://test-montagu"
        self.montagu_user = "test.montagu.user"
        self.montagu_password = "montagu_password"
        self.packit_url = PACKIT_URL


config = MockConfig()

def mock_auth(mock_montagu_api_class, requests_mock):
    mock_montagu_api = mock_montagu_api_class.return_value
    mock_montagu_api.token = "test-montagu-token"
    requests_mock.get(f"{PACKIT_URL}/api/auth/login/montagu", text = json.dumps({"token": "test-packit-token"} ))

@patch("montagu.MontaguAPI")
def test_authenticates_on_init(MockMontaguAPI, requests_mock):
    mock_auth(MockMontaguAPI, requests_mock)

    sut = PackitClient(config)

    MockMontaguAPI.assert_called_with("http://test-montagu", "test.montagu.user", "montagu_password")
    auth_call = requests_mock.request_history[0]
    assert auth_call.method == "GET"
    assert auth_call.url == f"{PACKIT_URL}/api/auth/login/montagu"
    assert auth_call.headers["Authorization"] == "Bearer test-montagu-token"
    assert sut.auth_success
    assert sut.token == "test-packit-token"


#@patch("montagu.MontaguAPI")
#def test_run():
#    mock_auth(MockMontaguAPI, requests_mock)

#def test_reauthenticates_on_401

#def test_raises_exception_on_unexpected_status

#def test_poll_status

@patch("montagu.MontaguAPI")
def test_kill_task(MockMontaguAPI, requests_mock):
    mock_auth(MockMontaguAPI, requests_mock)
    mock_kill_response = { "status": "dead" }
    requests_mock.post(f"{PACKIT_URL}/api/runner/cancel/test-task-id", text = json.dumps(mock_kill_response))

    sut = PackitClient(config)
    resp = sut.kill_task("test-task-id")

    assert resp == mock_kill_response
    req = requests_mock.request_history[1]
    assert req.headers["Authorization"] == "Bearer test-packit-token"

#def test_publish

