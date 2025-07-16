from YTClient.YTClient import YTClient
from YTClient.YTDataClasses import Project, Command

from src.task_run_diagnostic_reports import create_ticket
from src.config import ReportConfig, Config
from unittest.mock import call, Mock, patch
from test.unit.test_run_reports import MockConfig

fake_tags = [{"name": "g1"},
             {"name": "d1"},
             {"name": "t1"},
             {"name": "TEST"}]


def test_tags_created():
    report = ReportConfig("TEST", {}, ["to@example.com"],
                          "Hi", "a.ssignee", ["Funders"])
    mock_config: Config = MockConfig()
    mock_client = Mock(spec=YTClient("", ""))
    mock_client.create_issue = Mock(return_value="ISSUE")
    mock_client.get_issues = Mock(return_value=[])
    mock_client.get_tags = Mock(return_value=[])
    create_ticket("g1", "d1", "t1", "s1", report, "1234", None,
                  mock_client, mock_config)
    mock_client.create_tag.assert_has_calls(
        [call("d1"), call("g1"), call("t1"), call("TEST")])


def test_tags_not_created_if_exists():
    report = ReportConfig("TEST", {}, ["to@example.com"],
                          "Hi", "a.ssignee", ["Funders"])
    mock_config: Config = MockConfig()
    mock_client = Mock(spec=YTClient("", ""))
    mock_client.create_issue = Mock(return_value="ISSUE")
    mock_client.get_issues = Mock(return_value=[])
    mock_client.get_tags = Mock(return_value=fake_tags)
    create_ticket("g1", "d1", "t1", "s1", report, "1234", None,
                  mock_client, mock_config)
    mock_client.create_tag.assert_has_calls([])


def test_create_ticket_with_version():
    report = ReportConfig("TEST", {}, ["to@example.com"],
                          "Hi", "a.ssignee", ["Funders"])
    mock_config: Config = MockConfig()
    mock_client = Mock(spec=YTClient("", ""))
    mock_client.create_issue = Mock(return_value="ISSUE")
    mock_client.get_issues = Mock(return_value=[])
    mock_client.get_tags = Mock(return_value=fake_tags)
    create_ticket("g1", "d1", "t1", "s1", report, "1234", None,
                  mock_client, mock_config)
    expected_create = call(Project(id="78-0"),
                           "Check & share diag report with g1 (d1) t1",
                           "Report run triggered by upload to scenario: s1. "
                           "http://test-packit/TEST/1234/")
    mock_client.create_issue.assert_has_calls([expected_create])
    expected_command_query = \
        "for a.ssignee implementer a.ssignee tag g1 tag d1 tag t1 tag TEST"
    expected_command = call(Command(issues=["ISSUE"],
                                    query=expected_command_query))
    mock_client.run_command.assert_has_calls([expected_command])


def test_create_ticket_without_version():
    report = ReportConfig("TEST", {}, ["to@example.com"],
                          "Hi", "a.ssignee", ["Funders"])
    mock_config: Config = MockConfig()
    mock_client = Mock(spec=YTClient("", ""))
    mock_client.create_issue = Mock(return_value="ISSUE")
    mock_client.get_issues = Mock(return_value=[])
    mock_client.get_tags = Mock(return_value=fake_tags)
    create_ticket("g1", "d1", "t1", "s1", report, None, "Error message",
                  mock_client, mock_config)
    expected_create = call(Project(id="78-0"),
                           "Run, check & share diag report with g1 (d1) t1",
                           "Report run triggered by upload to scenario: s1. "
                           "Auto-run failed with error: Error message")
    mock_client.create_issue.assert_has_calls([expected_create])

    expected_command_query = \
        "for a.ssignee implementer a.ssignee tag g1 tag d1 tag t1 tag TEST"
    expected_command = call(Command(issues=["ISSUE"],
                                    query=expected_command_query))
    mock_client.run_command.assert_has_calls([expected_command])


@patch("src.task_run_diagnostic_reports.logging")
def test_create_ticket_logs_errors(logging):
    report = ReportConfig("TEST", {}, ["to@example.com"],
                          "Hi", "a.ssignee", ["Funders"])
    mock_config: Config = MockConfig()
    mock_client = Mock(spec=YTClient("", ""))
    mock_client.get_issues = Mock(return_value=[])
    mock_client.get_tags = Mock(return_value=fake_tags)
    test_ex = Exception("TEST EX")
    mock_client.create_issue = Mock(side_effect=test_ex)
    create_ticket("g1", "d1", "t1", "s1", report, "1234", None,
                  mock_client, mock_config)
    logging.exception.assert_has_calls([call(test_ex)])


def test_update_ticket():
    report = ReportConfig("TEST", {}, ["to@example.com"],
                          "Hi", "a.ssignee", ["Funders"])
    mock_config: Config = MockConfig()
    mock_client = Mock(spec=YTClient("", ""))
    mock_client.get_issues = Mock(return_value=["ISSUE"])
    mock_client.get_tags = Mock(return_value=fake_tags)
    create_ticket("g1", "d1", "t1", "s1", report, "1234", None,
                  mock_client, mock_config)
    expected_command = call("ISSUE",
                            "Check & share diag report with g1 (d1) t1",
                            "Report run triggered by upload to scenario: s1. "
                            "http://test-packit/TEST/1234/")
    mock_client.update_issue.assert_has_calls([expected_command])
