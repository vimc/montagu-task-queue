from src.config import Config, ReportConfig
from src.packit_client import PackitClient
from src.utils.run_reports import run_reports
from src.utils.running_reports_repository import RunningReportsRepository


def test_run_reports_handles_error():
    reports = [
        ReportConfig("nonexistent", None, ["test1@test.com"], "subject1",
                     "a.ssignee", ["Funders"]),
        ReportConfig("diagnostic", {}, ["test2@test.com"], "subject2",
                     "a.ssignee", ["Funders"])]
    config = Config()
    packit = PackitClient(config)
    success = {}
    error = {}

    def success_callback(report, version):
        success[report.name] = version

    def error_callback(report, message):
        error[report.name] = message

    running_reports_repository = RunningReportsRepository()

    versions = run_reports(packit, "testGroup", "testDisease",
                           "testTouchstone", config, reports,
                           success_callback, error_callback,
                           running_reports_repository)
    keys = list(versions.keys())
    assert len(keys) == 1
    assert versions[keys[0]]["published"] is True
    assert success["diagnostic"] == keys[0]
    assert "Failure for key" in error["nonexistent"]
    assert len(success) == 1
    assert len(error) == 1
