from src.task_run_diagnostic_reports import send_diagnostic_report_email
from src.config import ReportConfig
from unittest.mock import patch, call
from test.unit.test_run_reports import MockConfig

reports = [ReportConfig("r1", None, ["r1@example.com"], "Subj: r1",
                        1000),
           ReportConfig("r2", {"p1": "v1"}, ["r2@example.com"], "Subj: r2",
                        2000)]


@patch("src.task_run_diagnostic_reports.send_email")
def test_url_encodes_url_in_email(send_email):
    name = "'A silly, report"
    encoded = "%27A%20silly%2C%20report"
    report = ReportConfig(name, {}, ["to@example.com"], "Hi", 100)
    fake_emailer = {}
    mock_config = MockConfig()
    send_diagnostic_report_email(fake_emailer,
                                 report,
                                 "1234-abcd",
                                 "groupId",
                                 "diseaseId",
                                 "touchstoneId",
                                 mock_config)
    url = "http://orderly-web/report/{}/1234-abcd/".format(encoded, encoded)
    send_email.assert_has_calls([
        call(fake_emailer,
             report,
             "diagnostic_report",
             {
                 "report_version_url": url,
                 "disease": "diseaseId",
                 "group": "groupId",
                 "touchstone": "touchstoneId"
             },
             mock_config, list())])


@patch("src.task_run_diagnostic_reports.send_email")
def test_additional_recipients_used(send_email):
    name = "r1"
    report = ReportConfig(name, {}, ["to@example.com"], "Hi", 1000)
    fake_emailer = {}
    mock_config = MockConfig(use_additional_recipients=True)
    send_diagnostic_report_email(fake_emailer,
                                 report,
                                 "1234-abcd",
                                 "groupId",
                                 "diseaseId",
                                 "touchstoneId",
                                 mock_config,
                                 "someone@example.com")
    url = "http://orderly-web/report/{}/1234-abcd/".format(name)
    send_email.assert_has_calls([
        call(fake_emailer,
             report,
             "diagnostic_report",
             {
                 "report_version_url": url,
                 "disease": "diseaseId",
                 "group": "groupId",
                 "touchstone": "touchstoneId"
             },
             mock_config, ["someone@example.com"])])


@patch("src.task_run_diagnostic_reports.send_email")
def test_additional_recipients_not_used(send_email):
    name = "r1"
    report = ReportConfig(name, {}, ["to@example.com"], "Hi", 1000)
    fake_emailer = {}
    mock_config = MockConfig(use_additional_recipients=False)
    send_diagnostic_report_email(fake_emailer,
                                 report,
                                 "1234-abcd",
                                 "groupId",
                                 "diseaseId",
                                 "touchstoneId",
                                 mock_config,
                                 "someone@example.com")
    url = "http://orderly-web/report/{}/1234-abcd/".format(name)
    send_email.assert_has_calls([
        call(fake_emailer,
             report,
             "diagnostic_report",
             {
                 "report_version_url": url,
                 "disease": "diseaseId",
                 "group": "groupId",
                 "touchstone": "touchstoneId"
             },
             mock_config, list())])
