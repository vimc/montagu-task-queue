from src.task_run_diagnostic_reports import run_diagnostic_reports, \
    run_reports
from src.config import Config, ReportConfig


def test_run_diagnostic_reports():
    keys = run_diagnostic_reports("testGroup", "testDisease")
    assert len(keys) == 2


def test_run_reports_handles_error():
    reports = [ReportConfig("nonexistent", None), ReportConfig("minimal", {})]
    keys = run_reports(Config(), reports)
    assert len(keys) == 1
