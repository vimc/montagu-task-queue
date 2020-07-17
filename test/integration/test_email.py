from src.utils.email import Emailer


def test_send():
    emailer = Emailer("localhost", 1025)
    emailer.send("from@example.com",
                 ["to1@example.com", "to2@example.com"],
                 "New version of Orderly report: {report_name}",
                 "diagnostic_report",
                 {"report_name": "TEST REPORT",
                  "report_version_url": "http://test.com/test_report_version",
                  "report_params": "p1=v1, p2=v2"})
