import celery
import pytest
import time
import os

from YTClient.YTClient import YTClient
from YTClient.YTDataClasses import Command

from src.config import Config
from src.utils.running_reports_repository import RunningReportsRepository
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper

app = celery.Celery(broker="redis://guest@localhost//", backend="redis://")
sig = "run-diagnostic-reports"

yt_token = os.environ["YOUTRACK_TOKEN"]
yt = YTClient('https://mrc-ide.myjetbrains.com/youtrack/',
              token=yt_token)
test_touchstone = "touchstone-task-runner-test"


@pytest.fixture(autouse=True)
def cleanup_tickets():
    issues = yt.get_issues("tag: {}".format(test_touchstone))
    if len(issues) > 0:
        yt.run_command(Command(issues, "delete"))


def test_run_diagnostic_reports():
    versions = app.signature(sig,
                             ["testGroup",
                              "testDisease",
                              test_touchstone,
                              "2020-11-04T12:21:15",
                              "no_vaccination"]).delay().get()
    assert len(versions) == 2


def test_later_task_kills_earlier_task_report():
    # Check we don't have any rogue running reports
    running_repo = RunningReportsRepository(host="localhost")
    assert running_repo.get("testGroup", "testDisease", "diagnostic") is None

    app.send_task(sig, ["testGroup",
                        "testDisease",
                        test_touchstone,
                        "2020-11-04T12:21:15",
                        "no_vaccination"])

    # Poll the running report repository until the first task has saved its
    # running report key
    first_report_key = None
    tries = 0
    while first_report_key is None and tries < 60:
        time.sleep(0.5)
        first_report_key = running_repo.get("testGroup", "testDisease",
                                            "diagnostic")
        tries += 1

    assert first_report_key is not None

    versions = app.signature(sig,
                             ["testGroup",
                              "testDisease",
                              test_touchstone,
                              "2020-11-04T12:21:16",
                              "no_vaccination"]).delay().get()

    assert len(versions) == 2

    # Check first report key's status with OrderlyWeb - should have been killed
    config = Config()
    wrapper = OrderlyWebClientWrapper(config)
    result = wrapper.execute(wrapper.ow.report_status, first_report_key)
    assert result.status == "interrupted"
    assert result.finished

    # Check redis key has been tidied up
    assert running_repo.get("testGroup", "testDisease", "diagnostic") is None


def test_run_diagnostic_reports_nowait():
    app.send_task(sig, ["testGroup",
                        "testDisease",
                        test_touchstone,
                        "2020-11-04T12:21:15",
                        "no_vaccination"])
