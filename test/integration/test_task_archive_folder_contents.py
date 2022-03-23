from src.task_archive_folder_contents import archive_folder_contents
from test.integration.file_utils import write_text_file
import os


def test_run_archive_folder_contents():
    cwd = os.getcwd()
    local_folder = "{}/test_archive_files".format(cwd)

    write_text_file("{}/TestTaskFile1.csv".format(local_folder), "1,2,3")
    write_text_file("{}/TestTaskFile2.csv".format(local_folder), "a,b,c")

    assert len(os.listdir(local_folder)) == 2

    archive_folder_contents(local_folder)

    assert len(os.listdir(local_folder)) == 0
