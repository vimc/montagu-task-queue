from src.task_run_diagnostic_reports import run_reports
from src.config import ReportConfig
from orderlyweb_api import ReportStatusResult
from unittest.mock import patch, call

reports = [ReportConfig("r1", None), ReportConfig("r2", {"p1": "v1"})]


@patch("src.task_run_diagnostic_reports.logging")
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

    versions = run_reports(ow, MockConfig(), reports)

    assert versions == ["r1-version", "r2-version"]

    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Running report: r2. Key is r2-key"),
        call("Success for key r1-key. New version is r1-version"),
        call("Success for key r2-key. New version is r2-version")
    ], any_order=False)


@patch("src.task_run_diagnostic_reports.logging")
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

    versions = run_reports(ow, MockConfig(), reports)

    assert versions == ["r2-version", "r1-version"]

    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Running report: r2. Key is r2-key"),
        call("Success for key r2-key. New version is r2-version"),
        call("Success for key r1-key. New version is r1-version")
    ], any_order=False)

@patch("src.task_run_diagnostic_reports.logging")
def test_run_reports_with_run_error(logging):
    run_successfully = ["r2"]
    report_responses = {
       "r2-key": [ReportStatusResult({"status": "success",
                                      "version": "r2-version",
                                      "output": None})]
    }
    ow = MockOrderlyWebAPI(run_successfully, report_responses)

    versions = run_reports(ow, MockConfig(), reports)

    assert versions == ["r2-version"]
    logging.info.assert_has_calls([
        call("Running report: r2. Key is r2-key"),
        call("Success for key r2-key. New version is r2-version")
    ], any_order=False)
    args, kwargs = logging.exception.call_args
    assert str(args[0]) == "test-run-error: r1"


@patch("src.task_run_diagnostic_reports.logging")
def test_run_reports_with_status_error(logging):
    run_successfully = ["r1", "r2"]
    report_responses = {
        "r2-key": [ReportStatusResult({"status": "success",
                                       "version": "r2-version",
                                       "output": None})]
    }

    ow = MockOrderlyWebAPI(run_successfully, report_responses)

    versions = run_reports(ow, MockConfig(), reports)

    assert versions == ["r2-version"]
    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Running report: r2. Key is r2-key"),
        call("Success for key r2-key. New version is r2-version")
    ], any_order = False)
    args, kwargs = logging.exception.call_args
    assert str(args[0]) == "test-status-error: r1-key"


@patch("src.task_run_diagnostic_reports.logging")
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

    versions = run_reports(ow, MockConfig(), reports)

    assert versions == ["r1-version"]
    logging.info.assert_has_calls([
        call("Running report: r1. Key is r1-key"),
        call("Running report: r2. Key is r2-key"),
        call("Success for key r1-key. New version is r1-version")
    ], any_order = False)
    logging.error.assert_has_calls([
       call("Failure for key r2-key.")
    ], any_order = False)


class MockOrderlyWebAPI:
    def __init__(self, run_successfully, report_responses):
        self.run_successfully = run_successfully
        self.report_responses = report_responses

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


class MockConfig:
    @property
    def report_poll_seconds(self):
        return 1
