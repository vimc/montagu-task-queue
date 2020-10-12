from src.config import Config, ReportConfig
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper
from src.utils.run_reports import run_reports


def test_run_reports_handles_error():
    reports = [
        ReportConfig("nonexistent", None, ["test1@test.com"], "subject1", 600),
        ReportConfig("minimal", {}, ["test2@test.com"], "subject2", 600)]
    config = Config()
    wrapper = OrderlyWebClientWrapper(config)
    success = {}

    def success_callback(report, version):
        success[report.name] = version

    versions = run_reports(wrapper, config, reports, success_callback)
    keys = list(versions.keys())
    assert len(keys) == 1
    assert versions[keys[0]]["published"] is True
    assert success["minimal"] == keys[0]
    assert len(success) == 1
