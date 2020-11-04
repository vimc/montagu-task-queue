import pytest
from test.integration.fake_smtp_utils import FakeSmtpUtils, FakeEmailProperties
from src.utils.email import Emailer

smtp = FakeSmtpUtils()


@pytest.fixture(scope="module", autouse=True)
def mod_header(request):
    smtp.delete_all()


def test_send():
    emailer = Emailer("localhost", 1025, None, None)
    emailer.send("from@example.com",
                 ["to1@example.com", "to2@example.com"],
                 "VIMC diagnostic report: {touchstone} - {group} - {disease}",
                 "diagnostic_report",
                 {"disease": "d1",
                  "report_version_url": "http://test.com/test_report_version",
                  "touchstone": "tid",
                  "group": "G1",
                  "scenario": "no vaccination",
                  "utc_time": "Wed 04 Nov 2020 12:22:53 UTC",
                  "eastern_time": "Wed 04 Nov 2020 07:22:53 ET"
                  })

    expected_text = """Thank you for uploading your estimates for d1 """ + \
                    """for the tid touchstone.
This is an automated email with a link to your diagnostic report:

http://test.com/test_report_version

These estimates were received for scenario: no vaccination, on Wed 04 Nov 2020 12:22:53 UTC (Wed 04 Nov 2020 07:22:53 ET).

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
    Thank you for uploading your estimates for d1 for the tid touchstone.
    This is an automated email with a link to your diagnostic report:
</p>
<p>
    <a href="http://test.com/test_report_version">""" + \
                    """http://test.com/test_report_version</a>
</p>
<p>
    These estimates were received for scenario: no vaccination, on Wed 04 Nov 2020 12:22:53 UTC (Wed 04 Nov 2020 07:22:53 ET).
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

    smtp.assert_emails_match([FakeEmailProperties(
        "VIMC diagnostic report: tid - G1 - d1",
        ["to1@example.com", "to2@example.com"], "from@example.com",
        expected_text, expected_html)])
