from src.task_run_diagnostic_reports import run_diagnostic_reports, \
    run_reports, auth
from src.config import Config, ReportConfig
from test.integration.fake_smtp_utils import FakeSmtpUtils, FakeEmailProperties
import pytest


smtp = FakeSmtpUtils()


@pytest.fixture(scope="module", autouse=True)
def mod_header(request):
    smtp.delete_all()


def test_run_diagnostic_reports():
    versions = run_diagnostic_reports("testGroup", "testDisease")
    assert len(versions) == 2

    expected_text = """Hi

A new version of Orderly report {} is available to view at {}

This version was run with parameters: {}

Have a great day!"""

    expected_html = """ <html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
</head>
<body>
<p>Hi,</p>
<p>
    A new version of Orderly report {} is available to view """ +\
                    """<a href="{}">here</a>.
</p>
<p>
    This version was run with parameters: {}
</p>
<p>Have a great day!</p>
</body>
</html>"""

    report_1 = "minimal"
    report_2 = "other"
    url_template = "http://localhost:8888/report/{}/{}/"
    url_1 = url_template.format(report_1, versions[0])
    url_2 = url_template.format(report_2, versions[1])
    params_1 = "no parameters"
    params_2 = "nmin=0"
    smtp.assert_emails_match([
        FakeEmailProperties(
            "New version of Orderly report: minimal",
            ["minimal_modeller@example.com", "science@example.com"],
            "noreply@example.com",
            expected_text.format(report_1, url_1, params_1),
            expected_html.format(report_1, url_1, params_1)),
        FakeEmailProperties(
            "New version of another Orderly report: other",
            ["other_modeller@example.com", "science@example.com"],
            "noreply@example.com",
            expected_text.format(report_2, url_2, params_2),
            expected_html.format(report_2, url_2, params_2))
    ])


def test_run_reports_handles_error():
    reports = [
        ReportConfig("nonexistent", None, ["test1@test.com"], "subject1"),
        ReportConfig("minimal", {}, ["test2@test.com"], "subject2")]
    config = Config()
    orderly_web = auth(config)
    versions = run_reports(orderly_web, config, reports)
    assert len(versions) == 1


def test_run_reports_no_group_config():
    versions = run_diagnostic_reports("noGroup", "noDisease")
    assert len(versions) == 0


def test_run_reports_no_disease_config():
    versions = run_diagnostic_reports("testGroup", "noDisease")
    assert len(versions) == 0
