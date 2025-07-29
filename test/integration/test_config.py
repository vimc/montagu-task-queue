from src.config import Config

config = Config()


def test_host():
    assert config.host == "localhost"


def test_montagu_url():
    assert config.montagu_url == "http://localhost:8080"


def test_montagu_user():
    assert config.montagu_user == "test.user@example.com"


def test_montagu_password():
    assert config.montagu_password == "password"


def test_packit_url():
    assert config.packit_url == "https://localhost/packit"


def test_packit_disable_certificate_verify():
    assert config.packit_disable_certificate_verify


def test_youtrack_token():
    assert config.youtrack_token == "None"


def test_report_poll_seconds():
    assert config.report_poll_seconds == 5


def test_smtp_host():
    assert config.smtp_host == "localhost"


def test_smtp_port():
    assert config.smtp_port == 1025


def test_smtp_from():
    assert config.smtp_from == "noreply@example.com"


def test_smtp_user():
    assert config.smtp_user is None


def test_smtp_password():
    assert config.smtp_password is None


def test_diagnostic_reports():
    reports = config.diagnostic_reports("testGroup", "testDisease")
    assert len(reports) == 2

    assert reports[0].name == "diagnostic"
    assert len(reports[0].parameters.keys()) == 0
    assert reports[0].success_email_recipients == \
        ["minimal_modeller@example.com", "science@example.com"]
    assert reports[0].success_email_subject == \
        "VIMC diagnostic report: {touchstone} - {group} - {disease}"
    assert reports[0].publish_roles == ["minimal.modeller", "Funders"]

    assert reports[1].name == "diagnostic-param"
    assert reports[1].parameters == {"a": 1, "b": 2, "c": 3}
    assert reports[1].success_email_recipients == \
        ["other_modeller@example.com", "science@example.com"]
    assert reports[1].success_email_subject == \
        "New version of another Orderly report"
    assert reports[1].publish_roles == ["other.modeller"]


def test_diagnostic_reports_nonexistent():
    assert len(config.diagnostic_reports("not a group", "not a disease")) == 0
    assert len(config.diagnostic_reports("testGroup", "not a disease")) == 0


def test_archive_folder_contents_config():
    assert config.archive_folder_contents.min_file_age_seconds == 0
