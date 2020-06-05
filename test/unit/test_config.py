from src.config import Config

config = Config()


def test_broker():
    assert config.broker == "pyamqp://guest@localhost//"


def test_backend():
    assert config.backend == "rpc://"

