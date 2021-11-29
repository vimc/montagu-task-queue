from src.utils.run_reports import run_reports
from src.config import ReportConfig
from orderlyweb_api import ReportStatusResult
from unittest.mock import patch, call
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper
from test import ExceptionMatching
from test.unit.test_run_reports import MockConfig, MockRunningReportRepository

reports = [ReportConfig("r1", None, ["r1@example.com"],
                        "Subj: r1", 1000, "a.ssignee")]

report_response = ReportStatusResult({"status": "success",
                                      "version": "r1-version",
                                      "output": None})

group = "test_group"
disease = "test_disease"
touchstone = "2021test-1"


class MockOrderlyWebAPIWithExpiredToken:

    def run_report(self, name, params, timeout):
        raise Exception("Token expired")

    def report_status(self, key):
        raise Exception("Token expired")

    def publish_report(self, name, version):
        raise Exception("Token expired")


class MockOrderlyWebAPIWithValidToken:

    def run_report(self, name, params, timeout):
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

    mock_running_reports = MockRunningReportRepository()
    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, mock_running_reports)

    assert versions == {"r1-version": {"published": True, "report": "r1"}}
    logging.info.assert_has_calls([
        call("Running report: r1 with parameters touchstone=2021test-1,"
             " touchstone_name=2021test. "
             "Key is r1-key. Timeout is 1000s."),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version")
    ], any_order=False)

    assert success["called"] is True


@patch("src.utils.run_reports.logging")
@patch("src.orderlyweb_client_wrapper.logging")
def test_handles_auth_errors(logging_ow, logging_reports):
    wrapper = OrderlyWebClientWrapper({})
    success = {}

    def success_callback(report, version):
        success["called"] = True

    mock_running_reports = MockRunningReportRepository()
    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, mock_running_reports)

    # the wrapper will have an auth failure because no auth config
    # supplied
    expected_error = AttributeError(
        "'dict' object has no attribute 'montagu_url'")
    logging_ow.exception.assert_called_once_with(
        ExceptionMatching(expected_error))

    logging_reports.error.assert_called_once_with(
        "Orderlyweb authentication failed; could not begin task")

    assert len(success) == 0
    assert len(versions) == 0
