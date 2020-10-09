from src.utils.run_reports import run_reports
from src.config import ReportConfig
from orderlyweb_api import ReportStatusResult
from unittest.mock import patch, call
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper

reports = [ReportConfig("r1", None, ["r1@example.com"], "Subj: r1"),
           ReportConfig("r2", {"p1": "v1"}, ["r2@example.com"], "Subj: r2")]


@patch("src.utils.run_reports.logging")
def test_run_reports(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [ReportStatusResult({"status": "success",
                                       "version": "r1-version",
                                       "output": None})],
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }
    ow = MockOrderlyWebAPI(run_successfully, report_responses)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}

    def success_callback(report, version):
        success["called"] = True

    versions = run_reports(wrapper, MockConfig(), reports, success_callback)

    assert versions == {
        "r1-version": {"published": True},
        "r2-version": {"published": True}
    }

    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Running report: r2. Key is r2-key"),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version"),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version")
    ], any_order=False)

    assert success["called"] is True


@patch("src.utils.run_reports.logging")
def test_run_reports_with_additional_recipients(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [ReportStatusResult({"status": "success",
                                       "version": "r1-version",
                                       "output": None})],
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }
    ow = MockOrderlyWebAPI(run_successfully, report_responses)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}

    def success_callback(report, version):
        success["called"] = True

    versions = run_reports(wrapper, MockConfig(), reports, success_callback)

    assert versions == {
        "r1-version": {"published": True},
        "r2-version": {"published": True}
    }

    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Running report: r2. Key is r2-key"),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version"),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version")
    ], any_order=False)

    assert success["called"] is True


@patch("src.utils.run_reports.logging")
def test_run_reports_finish_on_different_poll_cycles(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [ReportStatusResult({"status": "running",
                                       "version": None,
                                       "output": None}),
                   ReportStatusResult({"status": "running",
                                       "version": None,
                                       "output": None}),
                   ReportStatusResult({"status": "success",
                                       "version": "r1-version",
                                       "output": None})
                   ],
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }
    ow = MockOrderlyWebAPI(run_successfully, report_responses)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}

    def success_callback(report, version):
        success["called"] = True

    versions = run_reports(wrapper, MockConfig(), reports, success_callback)

    assert versions == {
        "r2-version": {"published": True},
        "r1-version": {"published": True}
    }

    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Running report: r2. Key is r2-key"),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version"),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version")
    ], any_order=False)

    assert success["called"] is True


@patch("src.utils.run_reports.logging")
def test_run_reports_with_run_error(logging):
    run_successfully = ["r2"]
    report_responses = {
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }
    ow = MockOrderlyWebAPI(run_successfully, report_responses)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}

    def success_callback(report, version):
        success["called"] = True

    versions = run_reports(wrapper, MockConfig(), reports, success_callback)

    assert versions == {
        "r2-version": {"published": True}
    }

    logging.info.assert_has_calls([
        call("Running report: r2. Key is r2-key"),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version")
    ], any_order=False)
    args, kwargs = logging.exception.call_args
    assert str(args[0]) == "test-run-error: r1"
    assert success["called"] is True


@patch("src.utils.run_reports.logging")
def test_run_reports_with_status_error(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }

    ow = MockOrderlyWebAPI(run_successfully, report_responses)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}

    def success_callback(report, version):
        success["called"] = True

    versions = run_reports(wrapper, MockConfig(), reports, success_callback)

    assert versions == {
        "r2-version": {"published": True}
    }

    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Running report: r2. Key is r2-key"),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version")
    ], any_order=False)
    args, kwargs = logging.exception.call_args
    assert str(args[0]) == "test-status-error: r1-key"
    assert success["called"] is True


@patch("src.utils.run_reports.logging")
def test_run_reports_with_status_failure(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [ReportStatusResult({"status": "success",
                                       "version": "r1-version",
                                       "output": None})],
        "r2-key": [ReportStatusResult({"status": "error",
                                       "version": None,
                                       "output": None})]
    }

    ow = MockOrderlyWebAPI(run_successfully, report_responses)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}

    def success_callback(report, version):
        success["called"] = True

    versions = run_reports(wrapper, MockConfig(), reports, success_callback)

    assert versions == {
        "r1-version": {"published": True}
    }

    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Running report: r2. Key is r2-key"),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version")
    ], any_order=False)
    logging.error.assert_has_calls([
        call("Failure for key r2-key.")
    ], any_order=False)

    assert success["called"] is True


@patch("src.utils.run_reports.logging")
def test_run_reports_with_publish_failure(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [ReportStatusResult({"status": "success",
                                       "version": "r1-version",
                                       "output": None})],
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }
    fail_publish = ["r2"]
    ow = MockOrderlyWebAPI(run_successfully, report_responses, fail_publish)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}

    def success_callback(report, version):
        success["called"] = True

    versions = run_reports(wrapper, MockConfig(), reports, success_callback)

    assert versions == {
        "r1-version": {"published": True},
        "r2-version": {"published": False}
    }

    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Running report: r2. Key is r2-key"),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version"),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version")
    ], any_order=False)
    logging.error.assert_has_calls([
        call("Failed to publish report version r2-r2-version")
    ], any_order=False)

    assert success["called"] is True


class MockOrderlyWebAPI:
    def __init__(self, run_successfully, report_responses, fail_publish=None):
        if fail_publish is None:
            fail_publish = []
        self.run_successfully = run_successfully
        self.report_responses = report_responses
        self.fail_publish = fail_publish

    def run_report(self, name, params):
        if name in self.run_successfully:
            return name + "-key"
        else:
            raise Exception("test-run-error: " + name)

    def report_status(self, key):
        if key in self.report_responses and \
                len(self.report_responses[key]) > 0:
            return self.report_responses[key].pop(0)
        else:
            raise Exception("test-status-error: " + key)

    def publish_report(self, name, version):
        if name in self.fail_publish:
            raise Exception("Publish failed")
        else:
            return True


class MockConfig:

    def __init__(self, use_additional_recipients=True):
        self.use_additional_recipients = use_additional_recipients

    @property
    def report_poll_seconds(self):
        return 1

    @property
    def smtp_host(self):
        return "localhost"

    @property
    def smtp_port(self):
        return 25

    @property
    def smtp_from(self):
        return "test@test.com"

    @property
    def smtp_user(self):
        return None

    @property
    def smtp_password(self):
        return None

    @property
    def orderlyweb_url(self):
        return "http://orderly-web"
