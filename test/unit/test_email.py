from unittest.mock import patch, call
from src.utils.email import Emailer, send_email
from test import ExceptionMatching

test_template_values = {"disease": "d1",
                        "report_version_url":
                            "http://test.com/test_report_version",
                        "group": "group1",
                        "touchstone": "tid",
                        "scenario": "no vaccination",
                        "utc_time": "Wed 03 Nov 2020 12:21:53 UTC",
                        "eastern_time": "Wed 03 Nov 2020 07:21:53 ET"}


@patch("smtplib.SMTP")
def test_send_with_login(smtp):
    emailer = Emailer("remote.host", 1000, "username", "password")
    emailer.send("from@example.com",
                 ["to1@example.com"],
                 "New version of Orderly report",
                 "diagnostic_report",
                 test_template_values)
    smtp.return_value.login.assert_has_calls([
        call("username", "password"),
    ])


@patch("smtplib.SMTP")
def test_send_without_login(smtp):
    emailer = Emailer("remote.host", 1000, None, None)
    emailer.send("from@example.com",
                 ["to1@example.com"],
                 "New version of Orderly report",
                 "diagnostic_report",
                 test_template_values)
    smtp.return_value.login.assert_not_called()


@patch("src.utils.email.logging")
def test_send_handles_exceptions(logging):
    send_email(None, None, None, None, None, None)
    expected_error = AttributeError(
        "'NoneType' object has no attribute 'success_email_recipients'")
    logging.exception.assert_called_once_with(
        ExceptionMatching(expected_error))
