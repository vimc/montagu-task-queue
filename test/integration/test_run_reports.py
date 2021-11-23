from src.config import Config, ReportConfig
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper
from src.utils.run_reports import run_reports
from src.utils.running_reports_repository import RunningReportsRepository


def test_run_reports_handles_error():
    reports = [
        ReportConfig("nonexistent", None, ["test1@test.com"], "subject1", 600, "a.ssignee"),
        ReportConfig("diagnostic", {}, ["test2@test.com"], "subject2", 600, "a.ssignee")]
    config = Config()
    wrapper = OrderlyWebClientWrapper(config)
    success = {}

    def success_callback(report, version):
        success[report.name] = version

    running_reports_repository = RunningReportsRepository()

    versions = run_reports(wrapper, "testGroup", "testDisease",
                           "testTouchstone", config, reports,
                           success_callback, running_reports_repository)
    keys = list(versions.keys())
    assert len(keys) == 1
    assert versions[keys[0]]["published"] is True
    assert success["diagnostic"] == keys[0]
    assert len(success) == 1
