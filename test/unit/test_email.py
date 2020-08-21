from unittest.mock import patch, call
from src.utils.email import Emailer


@patch("smtplib.SMTP")
def test_send_with_login(smtp):
    emailer = Emailer("remote.host", 1000, "username", "password")
    emailer.send("from@example.com",
                 ["to1@example.com"],
                 "New version of Orderly report: {report_name}",
                 "diagnostic_report",
                 {"report_name": "TEST REPORT",
                  "report_version_url": "http://test.com/test_report_version",
                  "report_params": "p1=v1, p2=v2"})
    smtp.return_value.login.assert_has_calls([
        call("username", "password"),
    ])


@patch("smtplib.SMTP")
def test_send_without_login(smtp):
    emailer = Emailer("remote.host", 1000, None, None)
    emailer.send("from@example.com",
                 ["to1@example.com"],
                 "New version of Orderly report: {report_name}",
                 "diagnostic_report",
                 {"report_name": "TEST REPORT",
                  "report_version_url": "http://test.com/test_report_version",
                  "report_params": "p1=v1, p2=v2"})
    smtp.return_value.login.assert_not_called()
