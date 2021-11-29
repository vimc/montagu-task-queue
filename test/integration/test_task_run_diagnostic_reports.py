from unittest import mock
from unittest.mock import PropertyMock
import pytest

from src.task_run_diagnostic_reports import run_diagnostic_reports
from test.integration.fake_smtp_utils import FakeSmtpUtils, FakeEmailProperties
from test.integration.yt_utils import YouTrackUtils

smtp = FakeSmtpUtils()
yt = YouTrackUtils()


@pytest.fixture(scope="module", autouse=True)
def cleanup_emails():
    smtp.delete_all()


@pytest.fixture(autouse=True)
def cleanup_tickets(request):
    request.addfinalizer(yt.cleanup)


def test_run_diagnostic_reports():
    result = run_diagnostic_reports("testGroup",
                                    "testDisease",
                                    yt.test_touchstone,
                                    "2020-11-01T01:02:03",
                                    "s1",
                                    "estimate_uploader@example.com",
                                    "estimate_uploader2@example.com")
    versions = list(result.keys())
    assert len(versions) == 2

    expected_text = """Thank you for uploading your estimates for """ + \
                    """testDisease for the touchstone-task-runner-test""" + \
                    """ touchstone.
This is an automated email with a link to your diagnostic report:

{}

These estimates were received for scenario: s1, on Sun 01 Nov 2020 """ + \
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
                    """touchstone-task-runner-test touchstone.
    This is an automated email with a link to your diagnostic report:
</p>
<p>
    <a href="{}">{}</a>
</p>
<p>
    These estimates were received for scenario: s1, on Sun 01 Nov 2020 """ + \
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

    subject = "VIMC diagnostic report: {} - testGroup - testDisease" \
        .format(yt.test_touchstone)
    diagnostic_email_props = {
        "subject": subject,
        "recipients": ["minimal_modeller@example.com", "science@example.com",
                       "estimate_uploader@example.com",
                       "estimate_uploader2@example.com"]
    }

    diagnostic_param_email_props = {
        "subject": "New version of another Orderly report",
        "recipients": ["other_modeller@example.com", "science@example.com",
                       "estimate_uploader@example.com",
                       "estimate_uploader2@example.com"]
    }

    diagnostic_is_first = result[versions[0]]["report"] == "diagnostic"

    if diagnostic_is_first:
        report_1 = "diagnostic"
        report_2 = "diagnostic-param"
        email_props = [diagnostic_email_props, diagnostic_param_email_props]
    else:
        report_1 = "diagnostic-param"
        report_2 = "diagnostic"
        email_props = [diagnostic_param_email_props, diagnostic_email_props]

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
    versions = run_diagnostic_reports("noGroup", "noDisease",
                                      yt.test_touchstone,
                                      "2020-11-01 01:02:03", "s1")
    issues = yt.get_issues()
    assert len(versions) == 0
    assert len(issues) == 0


def test_run_reports_no_disease_config():
    versions = run_diagnostic_reports("testGroup", "noDisease",
                                      yt.test_touchstone,
                                      "2020-11-01 01:02:03", "s1")
    issues = yt.get_issues()
    assert len(versions) == 0
    assert len(issues) == 0


def test_ticket_created_on_success():
    result = run_diagnostic_reports("testGroup",
                                    "testDisease",
                                    yt.test_touchstone,
                                    "2020-11-01T01:02:03",
                                    "s1",
                                    "estimate_uploader@example.com")
    versions = list(result.keys())
    issues = yt.get_issues("summary: {}".format(yt.test_touchstone),
                           fields=["summary",
                                   "description",
                                   "tags(name)",
                                   "customFields(name,value(id,login))"])

    assert len(versions) == 2
    assert len(issues) == 2

    v1 = versions[0]
    r1 = result[v1]["report"]
    i1 = [i for i in issues if v1 in i["description"]][0]

    v2 = versions[1]
    r2 = result[v2]["report"]
    i2 = [i for i in issues if v2 in i["description"]][0]

    expected_summary = \
        "Check & share diag report with testGroup (testDisease) {}" \
        .format(yt.test_touchstone)
    expected_link1 = "http://localhost:8888/report/{}/{}/".format(r1, v1)
    assert i1["summary"] == expected_summary
    assert i1["description"] == expected_link1
    assignee = [f for f in i1["customFields"] if f["name"] == "Assignee"][0]
    assert assignee["value"]["login"] == \
           ("a.hill" if r1 == "diagnostic" else "e.russell")

    tags = [i["name"] for i in i1["tags"]]
    assert len(tags) == 3
    assert "testGroup" in tags
    assert "testDisease" in tags
    assert yt.test_touchstone in tags

    expected_link2 = "http://localhost:8888/report/{}/{}/".format(r2, v2)
    assert i2["summary"] == expected_summary
    assert i2["description"] == expected_link2
    assignee = [f for f in i2["customFields"] if f["name"] == "Assignee"][0]
    assert assignee["value"]["login"] == \
           ("a.hill" if r2 == "diagnostic" else "e.russell")

    tags = [i["name"] for i in i2["tags"]]
    assert len(tags) == 3
    assert "testGroup" in tags
    assert "testDisease" in tags
    assert yt.test_touchstone in tags


@mock.patch('src.config.Config.orderlyweb_url', new_callable=PropertyMock)
def test_ticket_created_on_error(mock_orderlyweb_url):
    mock_orderlyweb_url.return_value = "http://bad-url"
    result = run_diagnostic_reports("testGroup",
                                    "testDisease",
                                    yt.test_touchstone,
                                    "2020-11-01T01:02:03",
                                    "s1",
                                    "estimate_uploader@example.com")
    versions = list(result.keys())
    issues = yt.get_issues("tag: {}".format(yt.test_touchstone),
                           fields=["summary",
                                   "description",
                                   "tags(name)",
                                   "customFields(name,value(id,login))"])

    assert len(versions) == 0
    assert len(issues) == 2

    expected_summary = \
        "Run, check & share diag report with testGroup (testDisease) {}" \
        .format(yt.test_touchstone)

    i1 = issues[0]
    i2 = issues[1]

    assert i1["summary"] == expected_summary
    assert i1["description"] is None

    tags = [i["name"] for i in i1["tags"]]
    assert len(tags) == 3
    assert "testGroup" in tags
    assert "testDisease" in tags
    assert yt.test_touchstone in tags

    assert i2["summary"] == expected_summary
    assert i2["description"] is None

    tags = [i["name"] for i in i2["tags"]]
    assert len(tags) == 3
    assert "testGroup" in tags
    assert "testDisease" in tags
    assert yt.test_touchstone in tags
