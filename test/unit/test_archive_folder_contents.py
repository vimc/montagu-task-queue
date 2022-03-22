from src.task_archive_folder_contents import archive_folder_contents
from src.config import ArchiveFolderContentsConfig
from unittest.mock import patch, call, PropertyMock

mockArchiveTaskConfig = ArchiveFolderContentsConfig(10)
mockConfig = {
    "archive_folder_contents": mockArchiveTaskConfig
}

class MockFile:

    def __init__(self, path):
        self.path = path

mockFiles = [
    MockFile("/MockFile1.csv"),
    MockFile("/MockFile2.csv")
]


@patch("src.task_archive_folder_contents.Config.archive_folder_contents", new_callable=PropertyMock)
@patch("src.task_archive_folder_contents.time.time")
@patch("src.task_archive_folder_contents.os")
@patch("src.task_archive_folder_contents.logging")
def test_archives_only_files_older_than_configured_min_age(logging, os, time, archive_config):
    archive_config.return_value = mockArchiveTaskConfig
    time.return_value = 1000
    os.scandir.return_value = mockFiles
    os.path.getctime.side_effect = [985, 995]


    archive_folder_contents("test_folder")

    os.scandir.assert_called_once_with("test_folder")
    os.remove.assert_called_once_with("/MockFile1.csv")
    logging.info.assert_has_calls([
        call("Removing contents of test_folder:"),
        call("/MockFile1.csv"),
        call("/MockFile2.csv"),
        call("Not removing /MockFile2.csv as it is only 5 seconds old")
    ])


def test_handles_exception():
    test = "todo"