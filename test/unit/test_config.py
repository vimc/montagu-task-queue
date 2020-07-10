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

