import requests
import os
import pytest

from YTClient.YTClient import YTClient
from YTClient.YTDataClasses import Command

yt_token = os.environ["YOUTRACK_TOKEN"]
yt = YTClient('https://mrc-ide.myjetbrains.com/youtrack/',
              token=yt_token)
test_touchstone = "touchstone-task-runner-test"


@pytest.fixture(autouse=True)
def cleanup_tickets():
    issues = yt.get_issues("tag: {}".format(test_touchstone))
    if len(issues) > 0:
        yt.run_command(Command(issues, "delete"))


def test_run_task_through_flower():
    args = ["testGroup",
            "testDisease",
            test_touchstone,
            "2020-11-04T12:21:15",
            "no_vaccination"]
    result = requests.post(
        "http://localhost:5555/api/task/send-task/run-diagnostic-reports",
        json={"args": args}
    )
    assert result.status_code == 200
    assert result.json()["task-id"] > ""
    assert result.json()["state"] == "PENDING"
