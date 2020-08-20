from src.task_run_diagnostic_reports import run_reports
from src.config import ReportConfig
from orderlyweb_api import ReportStatusResult
from unittest.mock import patch, call
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper
from test.unit.test_task_run_diagnostic_reports import MockConfig

reports = [ReportConfig("r1", None, ["r1@example.com"], "Subj: r1")]

send_email_call_r1 = call(
    "test@test.com", ["r1@example.com"], "Subj: r1", "diagnostic_report",
    {"report_name": "r1",
     "report_version_url": "http://orderly-web/report/r1/r1-version/",
     "report_params": "no parameters"})

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


@patch("src.utils.email.Emailer.send")
@patch("src.task_run_diagnostic_reports.logging")
def test_retries_when_token_expired(logging, emailer_send):
    auth = MockReturnAuthorisedClient().auth
    wrapper = OrderlyWebClientWrapper(None, auth)
    versions = run_reports(wrapper, MockConfig(), reports)

    assert versions == ["r1-version"]
    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Success for key r1-key. New version is r1-version")
    ], any_order=False)

    emailer_send.assert_has_calls([send_email_call_r1])
