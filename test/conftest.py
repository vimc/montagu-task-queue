def pytest_addoption(parser):
    parser.addoption("--docker", action="store", default="false")