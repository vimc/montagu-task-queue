import celery
import pytest
import time
import os
import logging

from src.config import Config
from src.utils.running_reports_repository import RunningReportsRepository
from src.packit_client import PackitClient
from test.integration.yt_utils import YouTrackUtils
from test.integration.file_utils import write_text_file

app = celery.Celery(broker="redis://localhost//", backend="redis://")
reports_sig = "run-diagnostic-reports"
archive_folder_sig = "archive_folder_contents"
yt = YouTrackUtils()


@pytest.fixture(autouse=True)
def cleanup_tickets(request):
    request.addfinalizer(yt.cleanup)


@pytest.fixture(scope="session")
def docker(pytestconfig):
    return pytestconfig.getoption("docker")


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

    # Check first report key's status with Packit - should have been killed
    config = Config()
    packit = PackitClient(config)
    result = packit.poll(first_report_key)
    assert result["status"] == "CANCELLED"

    # Check redis key has been tidied up
    assert running_repo.get("testGroup", "testDisease", "diagnostic") is None


def test_archive_folder_contents(docker):
    # Write out files locally to folder which is bind mount when worker running
    # in docker
    cwd = os.getcwd()
    test_folder = "/test_archive_files"
    local_folder = "{}{}".format(cwd, test_folder)

    write_text_file("{}/TestWorkerFile1.csv".format(local_folder), "1,2,3")
    write_text_file("{}/TestWorkerFile2.csv".format(local_folder), "a,b,c")

    assert len(os.listdir(local_folder)) == 2

    # The folder param to the task depends on whether the worker is running in
    # docker - passed as a command line option to pytest
    folder_param = test_folder if docker == "true" else local_folder

    app.signature(archive_folder_sig,
                  [folder_param]).delay().get()

    # Check that files were removed
    assert len(os.listdir(local_folder)) == 0
