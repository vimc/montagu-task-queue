from src.task_run_archive_folder_contents import run_archive_folder_contents
from test.integration.file_utils import writeTextFile


def test_run_archive_folder_contents():
    cwd = os.getcwd()
    local_folder = "{}/test_archive_files".format(cwd)

    writeTextFile("{}/TestTaskFile1.csv".format(local_folder), "1,2,3")
    writeTextFile("{}/TestTaskFile2.csv".format(local_folder), "a,b,c")

    assert len(os.listdir(local_folder)) == 2

    test_archive_folder_contents(local_folder)

    assert len(os.listdir(local_folder)) == 0
