from src.utils.run_reports import run_reports
from src.config import ReportConfig
from orderlyweb_api import ReportStatusResult
from unittest.mock import patch, call, Mock
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper

reports = [ReportConfig("r1", None, ["r1@example.com"], "Subj: r1",
                        "a.ssignee", ["Funders"]),
           ReportConfig("r2", {"p1": "v1"}, ["r2@example.com"], "Subj: r2",
                        "a.ssignee", ["Tech"])]

expected_params = {
    "r1": {"touchstone": "2021test-1", "touchstone_name": "2021test"},
    "r2": {"p1": "v1", "touchstone": "2021test-1",
           "touchstone_name": "2021test"}
}

group = "test_group"
disease = "test_disease"
touchstone = "2021test-1"

expected_run_rpt_1_log = "Running report: r1 with parameters " \
                         "touchstone=2021test-1, touchstone_name=2021test. " \
                         "Key is r1-key."

expected_run_rpt_2_log = "Running report: r2 with parameters p1=v1, " \
                         "touchstone=2021test-1, touchstone_name=2021test. " \
                         "Key is r2-key."


@patch("src.utils.run_reports.logging")
def test_run_reports(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [{"status": "COMPLETE",
                    "packetId": "r1-version"}],
        "r2-key": [{"status": "COMPLETE",
                   "packetId": "r2-version"}]
    }

    packit = MockPackitClient(
        expected_params, run_successfully, report_responses)
    success_callback = Mock()
    error_callback = Mock()

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(packit, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    packit.refresh_git.assert_called_with()

    assert versions == {
        "r1-version": {"published": True, "report": "r1"},
        "r2-version": {"published": True, "report": "r2"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New packet id is r1-version"),
        call("Publishing report packet r1 (r1-version)"),
        call("Successfully published report packet r1 (r1-version)"),
        call("Success for key r2-key. New packet id is r2-version"),
        call("Publishing report packet r2 (r2-version)"),
        call("Successfully published report packet r2 (r2-version)")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    packit.kill_task.assert_not_called()

    success_callback.assert_has_calls([
        call(reports[0], "r1-version"),
        call(reports[1], "r2-version")
    ])
    error_callback.assert_not_called()


def test_run_reports_with_multi_hyphen_touchstone():
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [{"status": "COMPLETE",
                   "packetId": "r1-version"}],
        "r2-key": [{"status": "COMPLETE",
                   "packetId": "r2-version"}]
    }

    multi_touchstone = "2021test-extra-1"
    expected_multi_params = {
        "r1": {"touchstone": "2021test-extra-1",
               "touchstone_name": "2021test-extra"},
        "r2": {"p1": "v1", "touchstone": "2021test-extra-1",
               "touchstone_name": "2021test-extra"}
    }
    packit = MockPackitClient(expected_multi_params,
                              run_successfully, report_responses)
    success_callback = Mock()
    error_callback = Mock()

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(packit, group, disease, multi_touchstone,
                           MockConfig(), reports, success_callback,
                           error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"},
        "r2-version": {"published": True, "report": "r2"}
    }
    success_callback.assert_has_calls([
        call(reports[0], "r1-version"),
        call(reports[1], "r2-version")
    ])
    error_callback.assert_not_called()


@patch("src.utils.run_reports.logging")
def test_run_reports_kills_currently_running(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [{"status": "COMPLETE",
                   "packetId": "r1-version"}],
        "r2-key": [{"status": "COMPLETE",
                   "packetId": "r2-version"}]
    }

    packit = MockPackitClient(
        expected_params, run_successfully, report_responses)
    success_callback = Mock()
    error_callback = Mock()

    mock_running_reports = \
        MockRunningReportRepository(["r1-old-key", "r2-old-key"])

    versions = run_reports(packit, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"},
        "r2-version": {"published": True, "report": "r2"}
    }

    logging.info.assert_has_calls([
        call("Killing already running task: r1. Key is r1-old-key."),
        call(expected_run_rpt_1_log),
        call("Killing already running task: r2. Key is r2-old-key."),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New packet id is r1-version"),
        call("Publishing report packet r1 (r1-version)"),
        call("Successfully published report packet r1 (r1-version)"),
        call("Success for key r2-key. New packet id is r2-version"),
        call("Publishing report packet r2 (r2-version)"),
        call("Successfully published report packet r2 (r2-version)")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()

    packit.kill_task.assert_has_calls([
        call("r1-old-key"),
        call("r2-old-key")
    ], any_order=False)

    success_callback.assert_has_calls([
        call(reports[0], "r1-version"),
        call(reports[1], "r2-version")
    ])
    error_callback.assert_not_called()


@patch("src.utils.run_reports.logging")
def test_run_reports_finish_on_different_poll_cycles(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [{"status": "RUNNING", "packetId": None},
                   {"status": "RUNNING", "packetId": None},
                   {"status": "COMPLETE", "packetId": "r1-version"}
                   ],
        "r2-key": [{"status": "COMPLETE", "packetId": "r2-version"}]
    }
    packit = MockPackitClient(expected_params, run_successfully,
                              report_responses)
    success_callback = Mock()
    error_callback = Mock()

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(packit, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r2-version": {"published": True, "report": "r2"},
        "r1-version": {"published": True, "report": "r1"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r2-key. New packet id is r2-version"),
        call("Publishing report packet r2 (r2-version)"),
        call("Successfully published report packet r2 (r2-version)"),
        call("Success for key r1-key. New packet id is r1-version"),
        call("Publishing report packet r1 (r1-version)"),
        call("Successfully published report packet r1 (r1-version)")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    packit.kill_task.assert_not_called()

    success_callback.assert_has_calls([
        call(reports[1], "r2-version"),
        call(reports[0], "r1-version")
    ])
    error_callback.assert_not_called()


@patch("src.utils.run_reports.logging")
def test_run_reports_with_run_error(logging):
    run_successfully = ["r2"]
    report_responses = {
        "r2-key": [{"status": "COMPLETE",
                   "packetId": "r2-version"}]
    }
    packit = MockPackitClient(expected_params, run_successfully,
                              report_responses)
    success_callback = Mock()
    error_callback = Mock()

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(packit, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r2-version": {"published": True, "report": "r2"}
    }

    expected_err = "test-run-error: r1"
    logging.info.assert_has_calls([
        call(expected_run_rpt_2_log),
        call("Success for key r2-key. New packet id is r2-version"),
        call("Publishing report packet r2 (r2-version)"),
        call("Successfully published report packet r2 (r2-version)")
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

    packit.kill_task.assert_not_called()

    success_callback.assert_called_with(reports[1], "r2-version")
    error_callback.assert_called_with(reports[0], expected_err)


@patch("src.utils.run_reports.logging")
def test_run_reports_with_status_error(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r2-key": [{"status": "COMPLETE",
                   "packetId": "r2-version"}]
    }

    packit = MockPackitClient(expected_params, run_successfully,
                              report_responses)
    success_callback = Mock()
    error_callback = Mock()

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(packit, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r2-version": {"published": True, "report": "r2"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r2-key. New packet id is r2-version"),
        call("Publishing report packet r2 (r2-version)"),
        call("Successfully published report packet r2 (r2-version)")
    ], any_order=False)
    args, kwargs = logging.exception.call_args
    assert str(args[0]) == "test-status-error: r1-key"

    mock_running_reports.assert_expected_calls()
    packit.kill_task.assert_not_called()
    expected_err = "test-status-error: r1-key"
    success_callback.assert_called_with(reports[1], "r2-version")
    error_callback.assert_called_with(reports[0], expected_err)


@patch("src.utils.run_reports.logging")
def test_run_reports_with_status_failure(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [{"status": "COMPLETE",
                   "packetId": "r1-version"}],
        "r2-key": [{"status": "ERROR",
                   "packetId": None}]
    }

    packit = MockPackitClient(expected_params, run_successfully,
                              report_responses)
    success_callback = Mock()
    error_callback = Mock()

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(packit, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New packet id is r1-version"),
        call("Publishing report packet r1 (r1-version)"),
        call("Successfully published report packet r1 (r1-version)")
    ], any_order=False)
    logging.error.assert_has_calls([
        call("Failure for key r2-key. Status: ERROR")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    packit.kill_task.assert_not_called()
    success_callback.assert_called_with(reports[0], "r1-version")
    error_callback.assert_called_with(reports[1],
                                      "Failure for key r2-key. Status: ERROR")


@patch("src.utils.run_reports.logging")
def test_run_reports_with_run_cancelled(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [{"status": "COMPLETE",
                   "packetId": "r1-version"}],
        "r2-key": [{"status": "CANCELLED",
                   "packetId": None}]
    }

    packit = MockPackitClient(expected_params, run_successfully,
                              report_responses)
    success_callback = Mock()
    error_callback = Mock()

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(packit, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"}
    }

    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New packet id is r1-version"),
        call("Publishing report packet r1 (r1-version)"),
        call("Successfully published report packet r1 (r1-version)")
    ], any_order=False)
    logging.error.assert_has_calls([
        call("Failure for key r2-key. Status: CANCELLED")
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    packit.kill_task.assert_not_called()
    success_callback.assert_called_with(reports[0], "r1-version")
    # expect error callback not called for cancelled runs
    error_callback.assert_not_called()


@patch("src.utils.run_reports.logging")
def test_run_reports_with_publish_failure(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r1-key": [{"status": "COMPLETE",
                    "packetId": "r1-version"}],
        "r2-key": [{"status": "COMPLETE",
                    "packetId": "r2-version"}]
    }
    fail_publish = ["r2"]
    packit = MockPackitClient(expected_params, run_successfully,
                              report_responses, fail_publish)
    success_callback = Mock()
    error_callback = Mock()

    mock_running_reports = MockRunningReportRepository()

    versions = run_reports(packit, group, disease, touchstone, MockConfig(),
                           reports, success_callback, error_callback,
                           mock_running_reports)

    assert versions == {
        "r1-version": {"published": True, "report": "r1"},
        "r2-version": {"published": False, "report": "r2"}
    }

    expected_err = "Failed to publish report packet r2 (r2-version)"
    logging.info.assert_has_calls([
        call(expected_run_rpt_1_log),
        call(expected_run_rpt_2_log),
        call("Success for key r1-key. New packet id is r1-version"),
        call("Publishing report packet r1 (r1-version)"),
        call("Successfully published report packet r1 (r1-version)"),
        call("Success for key r2-key. New packet id is r2-version"),
        call("Publishing report packet r2 (r2-version)")
    ], any_order=False)
    logging.error.assert_has_calls([
        call(expected_err)
    ], any_order=False)

    mock_running_reports.assert_expected_calls()
    packit.kill_task.assert_not_called()
    success_callback.assert_called_with(reports[0], "r1-version")
    error_callback.assert_called_with(reports[1], expected_err)


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


class MockPackitClient:
    def __init__(self, expected_params, run_successfully, report_responses,
                 fail_publish=[]):
        self.auth_success = True
        self.expected_params = expected_params
        self.run_successfully = run_successfully
        self.report_responses = report_responses
        self.fail_publish = fail_publish
        self.kill_task = Mock()
        self.refresh_git = Mock()

    def run(self, name, params):
        assert params == self.expected_params[name]
        if name in self.run_successfully:
            return name + "-key"
        else:
            raise Exception("test-run-error: " + name)

    def poll(self, key):
        if key in self.report_responses and \
                len(self.report_responses[key]) > 0:
            return self.report_responses[key].pop(0)
        else:
            raise Exception("test-status-error: " + key)

    def publish(self, name, packit_id, roles):
        if name in self.fail_publish:
            raise Exception("Publish failed")
        else:
            return True


PACKIT_URL = "http://test-packit"


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
    def youtrack_token(self):
        return "12345"

    @property
    def packit_url(self):
        return PACKIT_URL

    @property
    def packit_disable_certificate_verify(self):
        return False

    @property
    def montagu_url(self):
        return "http://test-montagu"

    @property
    def montagu_user(self):
        return "test.montagu.user"

    @property
    def montagu_password(self):
        return "montagu_password"
