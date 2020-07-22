import pytest
from test.integration.fake_smtp_utils import FakeSmtpUtils, FakeEmailProperties
from src.utils.email import Emailer


smtp = FakeSmtpUtils()


@pytest.fixture(scope="module", autouse=True)
def mod_header(request):
    smtp.delete_all()


def test_send():
    emailer = Emailer("localhost", 1025)
    emailer.send("from@example.com",
                 ["to1@example.com", "to2@example.com"],
                 "New version of Orderly report: {report_name}",
                 "diagnostic_report",
                 {"report_name": "TEST REPORT",
                  "report_version_url": "http://test.com/test_report_version",
                  "report_params": "p1=v1, p2=v2"})

    expected_text = """Hi

A new version of Orderly report TEST REPORT is available to view at""" + \
                    """http://test.com/test_report_version

This version was run with parameters: p1=v1, p2=v2

Have a great day!"""

    expected_html = """ <html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
</head>
<body>
<p>Hi,</p>
<p>
    A new version of Orderly report TEST REPORT is available to view """ + \
                    """<a href="http://test.com/test_report_version">here</a>.
</p>
<p>
    This version was run with parameters: p1=v1, p2=v2
</p>
<p>Have a great day!</p>
</body>
</html>"""

    smtp.assert_emails_match([FakeEmailProperties(
        "New version of Orderly report: TEST REPORT",
        ["to1@example.com", "to2@example.com"], "from@example.com",
        expected_text, expected_html)])
