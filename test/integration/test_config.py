from src.config import Config

config = Config()


def test_broker():
    assert config.broker == "pyamqp://guest@localhost//"


def test_backend():
    assert config.backend == "rpc://"


def test_montagu_url():
    assert config.montagu_url == "http://localhost:8080"


def test_montagu_user():
    assert config.montagu_user == "test.user@example.com"


def test_montagu_password():
    assert config.montagu_password == "password"


def test_orderlyweb_url():
    assert config.orderlyweb_url == "http://localhost:8888"


def test_report_poll_seconds():
    assert config.report_poll_seconds == 5


def test_smtp_host():
    assert config.smtp_host == "localhost"


def test_smtp_port():
    assert config.smtp_port == 1025


def test_smtp_from():
    assert config.smtp_from == "noreply@example.com"


def test_diagnostic_reports():
    reports = config.diagnostic_reports("testGroup", "testDisease")
    assert len(reports) == 2

    assert reports[0].name == "minimal"
    assert len(reports[0].parameters.keys()) == 0
    assert reports[0].success_email_recipients == \
           ["minimal_modeller@example.com", "science@example.com"]
    assert reports[0].success_email_subject == "New version of Orderly report: {report_name}"

    assert reports[1].name == "other"
    assert len(reports[1].parameters.keys()) == 1
    assert reports[1].parameters["nmin"] == 0
    assert reports[1].success_email_recipients == \
        ["other_modeller@example.com", "science@example.com"]
    assert reports[1].success_email_subject == "New version of another Orderly report: {report_name}"


def test_diagnostic_reports_nonexistent():
    assert len(config.diagnostic_reports("not a group", "not a disease")) == 0
    assert len(config.diagnostic_reports("testGroup", "not a disease")) == 0
