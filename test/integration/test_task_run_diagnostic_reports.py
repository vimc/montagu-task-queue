from src.task_run_diagnostic_reports import run_diagnostic_reports
from test.integration.fake_smtp_utils import FakeSmtpUtils, FakeEmailProperties
import pytest

smtp = FakeSmtpUtils()


@pytest.fixture(scope="module", autouse=True)
def mod_header(request):
    smtp.delete_all()


def test_run_diagnostic_reports():
    result = run_diagnostic_reports("testGroup",
                                    "testDisease",
                                    "tid",
                                    "2020-11-01T01:02:03",
                                    "s1",
                                    "estimate_uploader@example.com",
                                    "estimate_uploader2@example.com")
    versions = list(result.keys())
    assert len(versions) == 2

    expected_text = """Thank you for uploading your estimates for """ + \
                    """testDisease for the tid touchstone.
This is an automated email with a link to your diagnostic report:

{}

These estimates were received for scenario: s1, on Sun 01 Nov 2020 """ +\
                    """01:02:03 UTC (Sat 31 Oct 2020 20:02:03 ET).

Please reply to this email to let us know:
- whether the estimates in the report make sense to you
- whether you'd like VIMC to accept these estimates, or if you will """ + \
                    """need to provide re-runs
"""

    expected_html = """<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
</head>
<body>
<p>
    Thank you for uploading your estimates for testDisease for the """ + \
                    """tid touchstone.
    This is an automated email with a link to your diagnostic report:
</p>
<p>
    <a href="{}">{}</a>
</p>
<p>
    These estimates were received for scenario: s1, on Sun 01 Nov 2020 """ +\
                    """01:02:03 UTC (Sat 31 Oct 2020 20:02:03 ET).
</p>
<p>
    Please reply to this email to let us know:
</p>
<ul>
    <li>
        whether the estimates in the report make sense to you
    </li>
    <li>
        whether you'd like VIMC to accept these estimates, or if you """ + \
                    """will need to provide re-runs
    </li>
</ul>
</body>
</html>"""

    minimal_email_props = {
        "subject": "VIMC diagnostic report: tid - testGroup - testDisease",
        "recipients": ["minimal_modeller@example.com", "science@example.com",
                       "estimate_uploader@example.com",
                       "estimate_uploader2@example.com"]
    }

    other_email_props = {
        "subject": "New version of another Orderly report",
        "recipients": ["other_modeller@example.com", "science@example.com",
                       "estimate_uploader@example.com",
                       "estimate_uploader2@example.com"]
    }

    minimal_is_first = result[versions[0]]["report"] == "minimal"

    if minimal_is_first:
        report_1 = "minimal"
        report_2 = "other"
        email_props = [minimal_email_props, other_email_props]
    else:
        report_1 = "other"
        report_2 = "minimal"
        email_props = [other_email_props, minimal_email_props]

    url_template = "http://localhost:8888/report/{}/{}/"
    url_1 = url_template.format(report_1, versions[0])
    url_2 = url_template.format(report_2, versions[1])

    smtp.assert_emails_match([
        FakeEmailProperties(
            email_props[0]["subject"],
            email_props[0]["recipients"],
            "noreply@example.com",
            expected_text.format(url_1),
            expected_html.format(url_1, url_1)),
        FakeEmailProperties(
            email_props[1]["subject"],
            email_props[1]["recipients"],
            "noreply@example.com",
            expected_text.format(url_2),
            expected_html.format(url_2, url_2))
    ])


def test_run_reports_no_group_config():
    versions = run_diagnostic_reports("noGroup", "noDisease", "t1",
                                      "2020-11-01 01:02:03", "s1")
    assert len(versions) == 0


def test_run_reports_no_disease_config():
    versions = run_diagnostic_reports("testGroup", "noDisease", "t1",
                                      "2020-11-01 01:02:03", "s1")
    assert len(versions) == 0
