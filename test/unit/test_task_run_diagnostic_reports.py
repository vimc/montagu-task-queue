from src.task_run_diagnostic_reports import run_diagnostic_reports, \
    run_reports
from src.config import Config, ReportConfig


def test_run_diagnostic_reports():
    versions = run_diagnostic_reports("testGroup", "testDisease")
    assert len(versions) == 2


def test_run_reports_handles_error():
    reports = [ReportConfig("nonexistent", None), ReportConfig("minimal", {})]
    versions = run_reports(Config(), reports)
    assert len(versions) == 1


def test_run_reports_no_group_config():
    versions = run_diagnostic_reports("noGroup", "noDisease")
    assert len(versions) == 0


def test_run_reports_no_disease_config():
    versions = run_diagnostic_reports("testGroup", "noDisease")
    assert len(versions) == 0
