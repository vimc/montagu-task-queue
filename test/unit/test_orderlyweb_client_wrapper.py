from src.utils.run_reports import run_reports
from src.config import ReportConfig
from orderlyweb_api import ReportStatusResult
from unittest.mock import patch, call
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper
from test.unit.test_run_reports import MockConfig

reports = [ReportConfig("r1", None, ["r1@example.com"], "Subj: r1")]

report_response = ReportStatusResult({"status": "success",
                                      "version": "r1-version",
                                      "output": None})


class MockOrderlyWebAPIWithExpiredToken:

    def run_report(self, name, params):
        raise Exception("Token expired")

    def report_status(self, key):
        raise Exception("Token expired")

    def publish_report(self, name, version):
        raise Exception("Token expired")


class MockOrderlyWebAPIWithValidToken:

    def run_report(self, name, params):
        return "r1-key"

    def report_status(self, key):
        return report_response

    def publish_report(self, name, version):
        return True


class MockReturnAuthorisedClient:
    def __init__(self):
        self.callCount = 0

    def auth(self, config):
        if self.callCount == 0:
            self.callCount = 1
            # if this is the first call, return an expired token error
            return MockOrderlyWebAPIWithExpiredToken()
        else:
            # on the second call, return success reponses
            return MockOrderlyWebAPIWithValidToken()


@patch("src.utils.run_reports.logging")
def test_retries_when_token_expired(logging):
    auth = MockReturnAuthorisedClient().auth
    wrapper = OrderlyWebClientWrapper(None, auth)
    success = {}

    def success_callback(report, version):
        success["called"] = True

    versions = run_reports(wrapper, MockConfig(), reports, success_callback)

    assert versions == {"r1-version": {"published": True}}
    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version")
    ], any_order=False)

    assert success["called"] is True
