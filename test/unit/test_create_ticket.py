from YTClient.YTClient import YTClient
from YTClient.YTDataClasses import Project, Command

from src.task_run_diagnostic_reports import create_ticket
from src.config import ReportConfig, Config
from unittest.mock import call, Mock, patch
from test.unit.test_run_reports import MockConfig


def test_create_ticket():
    report = ReportConfig("TEST", {}, ["to@example.com"],
                          "Hi", 100, "a.ssignee")
    mock_config: Config = MockConfig()
    mock_client = Mock(spec=YTClient("", ""))
    mock_client.create_issue = Mock(return_value="ISSUE")
    create_ticket("g1", "d1", "t1", report, "1234", mock_client, mock_config)
    expected_create = call(Project(id="78-0"),
                           "Check & share diag report with g1 (d1) t1",
                           "http://orderly-web/report/TEST/1234/")
    mock_client.create_issue.assert_has_calls([expected_create])
    expected_command_query = "for a.ssignee tag g1 tag d1 tag t1"
    expected_command = call(Command(issues=["ISSUE"],
                                    query=expected_command_query))
    mock_client.run_command.assert_has_calls([expected_command])


@patch("src.task_run_diagnostic_reports.logging")
def test_create_ticket_logs_errors(logging):
    report = ReportConfig("TEST", {}, ["to@example.com"],
                          "Hi", 100, "a.ssignee")
    mock_config: Config = MockConfig()
    mock_client = Mock(spec=YTClient("", ""))
    test_ex = Exception("TEST EX")
    mock_client.create_issue = Mock(side_effect=test_ex)
    create_ticket("g1", "d1", "t1", report, "1234", mock_client, mock_config)
    logging.exception.assert_has_calls([call(test_ex)])
