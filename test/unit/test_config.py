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


def test_diagnostic_reports():
    reports = config.diagnostic_reports("testGroup", "testDisease")
    assert len(reports) == 2
    assert reports[0].name == "minimal"
    assert len(reports[0].parameters.keys()) == 0
    assert reports[1].name == "other"
    assert len(reports[1].parameters.keys()) == 2
    assert reports[1].parameters["nmin"] == 0
    assert reports[1].parameters["type"] == "test"


def test_diagnostic_reports_nonexistent():
    assert len(config.diagnostic_reports("not a group", "not a disease")) == 0
    assert len(config.diagnostic_reports("testGroup", "not a disease")) == 0
