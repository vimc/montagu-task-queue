import celery
import pytest
import time
import os

from src.config import Config
from src.utils.running_reports_repository import RunningReportsRepository
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper
from test.integration.yt_utils import YouTrackUtils

app = celery.Celery(broker="redis://guest@localhost//", backend="redis://")
reports_sig = "run-diagnostic-reports"
archive_folder_sig = "archive_folder_contents"
yt = YouTrackUtils()


@pytest.fixture(autouse=True)
def cleanup_tickets(request):
    request.addfinalizer(yt.cleanup)


def test_run_diagnostic_reports():
    versions = app.signature(reports_sig,
                             ["testGroup",
                              "testDisease",
                              yt.test_touchstone,
                              "2020-11-04T12:21:15",
                              "no_vaccination"]).delay().get()
    assert len(versions) == 2


def test_later_task_kills_earlier_task_report():
    # Check we don't have any rogue running reports
    running_repo = RunningReportsRepository(host="localhost")
    assert running_repo.get("testGroup", "testDisease", "diagnostic") is None

    app.send_task(reports_sig, ["testGroup",
                        "testDisease",
                        yt.test_touchstone,
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

    versions = app.signature(reports_sig,
                             ["testGroup",
                              "testDisease",
                              yt.test_touchstone,
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


def test_archive_folder_contents():
    # Write out files locally to folder which is bind mount when worker running
    # in docker
    cwd = os.getcwd()
    local_folder = "{}/test_archive_files".format(cwd)

    with open("{}/TestFile1.csv".format(local_folder), 'w') as file:
        file.write("1,2,3")

    with open("{}/TestFile2.csv".format(local_folder), 'w') as file:
        file.write("a,b,c")

    assert len(os.listdir(local_folder)) == 2


    # TODO: This will be different if not running for docker - it will be the same as local_folder
    folder_param = "/test_archive_files"

    app.signature(archive_folder_sig,
                  [folder_param]).delay().get()

    # Check that files were removed
    assert len(os.listdir(local_folder)) == 0
