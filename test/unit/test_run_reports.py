from src.utils.run_reports import run_reports
from src.config import ReportConfig
from orderlyweb_api import ReportStatusResult
from unittest.mock import patch, call, Mock
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper

reports = [ReportConfig("r1", None, ["r1@example.com"], "Subj: r1",
                        1000, "a.ssignee"),
           ReportConfig("r2", {"p1": "v1"}, ["r2@example.com"], "Subj: r2",
                        2000, "a.ssignee")]

expected_params = {
    "r1": {"touchstone": "2021test-1", "touchstone_name": "2021test"},
    "r2": {"p1": "v1", "touchstone": "2021test-1",
           "touchstone_name": "2021test"}
}

expected_timeouts = {
    "r1": 1000,
    "r2": 2000
}

group = "test_group"
disease = "test_disease"
touchstone = "2021test-1"

expected_run_rpt_1_log = "Running report: r1 with parameters " \
                         "touchstone=2021test-1, touchstone_name=2021test. " \
                         "Key is r1-key. Timeout is 1000s."

expected_run_rpt_2_log = "Running report: r2 with parameters p1=v1, " \
                         "touchstone=2021test-1, touchstone_name=2021test. " \
                         "Key is r2-key. Timeout is 2000s."


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

    ow = MockOrderlyWebAPI(run_successfully, report_responses,
                           expected_params, expected_timeouts)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}
    error = {"called": False}

    def success_callback(report, version):
        success["called"] = True

    def error_callback(report, message):
        error["called"] = message

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"},
        "r2-version": {"published": True, "report": "r2"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version"),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    ow.kill_report.assert_not_called()

    assert success["called"] is True
    assert error["called"] is False


def test_run_reports_with_multi_hyphen_touchstone():
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [ReportStatusResult({"status": "success",
                                       "version": "r1-version",
                                       "output": None})],
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }

    multi_touchstone = "2021test-extra-1"
    expected_multi_params = {
        "r1": {"touchstone": "2021test-extra-1",
               "touchstone_name": "2021test-extra"},
        "r2": {"p1": "v1", "touchstone": "2021test-extra-1",
               "touchstone_name": "2021test-extra"}
    }
    ow = MockOrderlyWebAPI(run_successfully, report_responses,
                           expected_multi_params, expected_timeouts)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)

    success = {}
    error = {"called": False}

    def success_callback(report, version):
        success["called"] = True

    def error_callback(report, message):
        error["called"] = message

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(wrapper, group, disease, multi_touchstone,
                           MockConfig(), reports, success_callback,
                           error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"},
        "r2-version": {"published": True, "report": "r2"}
    }
    assert success["called"] is True
    assert error["called"] is False


@patch("src.utils.run_reports.logging")
def test_run_reports_kills_currently_running(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [ReportStatusResult({"status": "success",
                                       "version": "r1-version",
                                       "output": None})],
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }

    ow = MockOrderlyWebAPI(run_successfully, report_responses,
                           expected_params, expected_timeouts)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}
    error = {"called": False}

    def success_callback(report, version):
        success["called"] = True

    def error_callback(report, message):
        error["called"] = message

    mock_running_reports = \
        MockRunningReportRepository(["r1-old-key", "r2-old-key"])

    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"},
        "r2-version": {"published": True, "report": "r2"}
    }

    logging.info.assert_has_calls([
        call("Killing already running report: r1. Key is r1-old-key"),
        call(expected_run_rpt_1_log),
        call("Killing already running report: r2. Key is r2-old-key"),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version"),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()

    ow.kill_report.assert_has_calls([
        call("r1-old-key"),
        call("r2-old-key")
    ], any_order=False)

    assert success["called"] is True
    assert error["called"] is False


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

    ow = MockOrderlyWebAPI(run_successfully, report_responses,
                           expected_params, expected_timeouts)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}
    error = {"called": False}

    def success_callback(report, version):
        success["called"] = True

    def error_callback(report, message):
        error["called"] = message

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"},
        "r2-version": {"published": True, "report": "r2"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version"),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    ow.kill_report.assert_not_called()

    assert success["called"] is True
    assert error["called"] is False


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
    ow = MockOrderlyWebAPI(run_successfully, report_responses,
                           expected_params, expected_timeouts)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}
    error = {"called": False}

    def success_callback(report, version):
        success["called"] = True

    def error_callback(report, message):
        error["called"] = message

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r2-version": {"published": True, "report": "r2"},
        "r1-version": {"published": True, "report": "r1"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version"),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    ow.kill_report.assert_not_called()

    assert success["called"] is True
    assert error["called"] is False


@patch("src.utils.run_reports.logging")
def test_run_reports_with_run_error(logging):
    run_successfully = ["r2"]
    report_responses = {
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }
    ow = MockOrderlyWebAPI(run_successfully, report_responses,
                           expected_params, expected_timeouts)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}
    error = {"called": False}

    def success_callback(report, version):
        success["called"] = True

    def error_callback(report, message):
        error["called"] = message

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r2-version": {"published": True, "report": "r2"}
    }

    expected_err = "test-run-error: r1"
    logging.info.assert_has_calls([
        call(expected_run_rpt_2_log),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version")
    ], any_order=False)
    args, kwargs = logging.exception.call_args
    assert str(args[0]) == expected_err

    # Different from standard set of expected calls, as error running r1
    mock_running_reports.get.assert_has_calls([
        call(group, disease, "r1"),
        call(group, disease, "r2")
    ], any_order=False)

    mock_running_reports.set.assert_has_calls([
        call(group, disease, "r2", "r2-key")
    ], any_order=False)

    mock_running_reports.delete_if_matches.assert_has_calls([
        call(group, disease, "r2", "r2-key")
    ], any_order=False)

    ow.kill_report.assert_not_called()

    assert success["called"] is True
    assert error["called"] == expected_err


@patch("src.utils.run_reports.logging")
def test_run_reports_with_status_error(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }

    ow = MockOrderlyWebAPI(run_successfully, report_responses,
                           expected_params, expected_timeouts)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}
    error = {"called": False}

    def success_callback(report, version):
        success["called"] = version

    def error_callback(report, message):
        error["called"] = message

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r2-version": {"published": True, "report": "r2"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version"),
        call("Successfully published report version r2-r2-version")
    ], any_order=False)
    args, kwargs = logging.exception.call_args
    assert str(args[0]) == "test-status-error: r1-key"

    mock_running_reports.assert_expected_calls()
    ow.kill_report.assert_not_called()
    expected_err = "test-status-error: r1-key"
    assert success["called"] == "r2-version"
    assert error["called"] == expected_err


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

    ow = MockOrderlyWebAPI(run_successfully, report_responses,
                           expected_params, expected_timeouts)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}
    error = {"called": False}

    def success_callback(report, version):
        success["called"] = version

    def error_callback(report, message):
        error["called"] = message

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version")
    ], any_order=False)
    logging.error.assert_has_calls([
        call("Failure for key r2-key. Status: error")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    ow.kill_report.assert_not_called()
    assert success["called"] == "r1-version"
    assert error["called"] == "Failure for key r2-key. Status: error"


@patch("src.utils.run_reports.logging")
def test_run_reports_with_run_cancelled(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [ReportStatusResult({"status": "success",
                                       "version": "r1-version",
                                       "output": None})],
        "r2-key": [ReportStatusResult({"status": "interrupted",
                                       "version": None,
                                       "output": None})]
    }

    ow = MockOrderlyWebAPI(run_successfully, report_responses,
                           expected_params, expected_timeouts)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}
    error = {"called": False}

    def success_callback(report, version):
        success["called"] = version

    def error_callback(report, message):
        error["called"] = message

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version")
    ], any_order=False)
    logging.error.assert_has_calls([
        call("Failure for key r2-key. Status: interrupted")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    ow.kill_report.assert_not_called()
    assert success["called"] == "r1-version"
    # expect error callback not called for cancelled runs
    assert error["called"] is False


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
    ow = MockOrderlyWebAPI(run_successfully, report_responses,
                           expected_params, expected_timeouts, fail_publish)
    wrapper = OrderlyWebClientWrapper(None, lambda x: ow)
    success = {}
    error = {}

    def success_callback(report, version):
        success["called"] = version

    def error_callback(report, message):
        error["called"] = message

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(wrapper, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"},
        "r2-version": {"published": False, "report": "r2"}
    }

    expected_err = "Failed to publish report version r2-r2-version"
    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New version is r1-version"),
        call("Publishing report version r1-r1-version"),
        call("Successfully published report version r1-r1-version"),
        call("Success for key r2-key. New version is r2-version"),
        call("Publishing report version r2-r2-version")
    ], any_order=False)
    logging.error.assert_has_calls([
        call(expected_err)
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    ow.kill_report.assert_not_called()
    assert success["called"] == "r1-version"
    assert error["called"] == expected_err


class MockRunningReportRepository:
    def __init__(self, get_responses=[None, None]):
        self.set = Mock()
        self.delete_if_matches = Mock()
        self.get = Mock(side_effect=get_responses)

    def assert_expected_calls(self):
        self.get.assert_has_calls([
            call(group, disease, "r1"),
            call(group, disease, "r2")
        ], any_order=False)

        self.set.assert_has_calls([
            call(group, disease, "r1", "r1-key"),
            call(group, disease, "r2", "r2-key")
        ], any_order=False)

        self.delete_if_matches([
            call(group, disease, "r1", "r1-key"),
            call(group, disease, "r2", "r2-key")
        ], any_order=False)


class MockOrderlyWebAPI:
    def __init__(self, run_successfully, report_responses, expected_params,
                 expected_timeouts, fail_publish=None):
        if fail_publish is None:
            fail_publish = []
        self.run_successfully = run_successfully
        self.report_responses = report_responses
        self.expected_params = expected_params
        self.expected_timeouts = expected_timeouts
        self.fail_publish = fail_publish
        self.kill_report = Mock()

    def run_report(self, name, params, timeout):
        assert params == self.expected_params[name]
        assert timeout == self.expected_timeouts[name]
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

    @property
    def youtrack_token(self):
        return "12345"
