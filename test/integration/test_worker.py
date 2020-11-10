import celery
import time
from src.config import Config
from src.utils.running_reports_repository import RunningReportsRepository
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper

app = celery.Celery(broker="redis://guest@localhost//", backend="rpc://")
sig = "run-diagnostic-reports"


def test_run_diagnostic_reports():
    versions = app.signature(sig,
                             ["testGroup",
                              "testDisease",
                              "touchstone",
                              "2020-11-04T12:21:15",
                              "no_vaccination"]).delay().get()
    assert len(versions) == 2


def test_run_diagnostic_reports_nowait():
    app.send_task(sig, ["testGroup",
                        "testDisease",
                        "touchstone",
                        "2020-11-04T12:21:15",
                        "no_vaccination"])


def test_later_task_kills_earlier_task_report():
    running_repo = RunningReportsRepository(host="localhost")
    app.send_task(sig, ["testGroup",
                        "testDisease",
                        "touchstone",
                        "2020-11-04T12:21:15",
                        "no_vaccination"])

    # Poll the running report repository until the first task has saved its
    # running report key
    first_report_key = None
    tries = 0
    while first_report_key is None and tries < 60:
        time.sleep(1)
        first_report_key = running_repo.get("testGroup", "testDisease", "minimal")
        tries += 1

    assert first_report_key is not None

    versions = app.signature(sig,
                             ["testGroup",
                              "testDisease",
                              "touchstone",
                              "2020-11-04T12:21:16",
                              "no_vaccination"]).delay().get()
    assert len(versions) == 2

    # Check first report key's status with OrderlyWeb - should have been killed
    config = Config()
    wrapper = OrderlyWebClientWrapper(config)
    result = wrapper.execute(wrapper.ow.report_status, first_report_key)
    assert result.status == "killed"
    assert result.finished == True

    # Check redis key has been tidied up
    assert running_repo.get("testGroup", "testDisease", "minimal") is None



