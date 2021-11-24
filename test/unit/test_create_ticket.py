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
    expected_assign = call(Command(issues=["ISSUE"],
                                   query="Assignee a.ssignee"))
    expected_tag_group = call(Command(issues=["ISSUE"],
                                      query="tag g1"))
    expected_tag_disease = call(Command(issues=["ISSUE"],
                                        query="tag d1"))
    expected_tag_touchstone = call(Command(issues=["ISSUE"],
                                           query="tag t1"))
    mock_client.run_command.assert_has_calls([expected_assign,
                                              expected_tag_group,
                                              expected_tag_disease,
                                              expected_tag_touchstone])


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
