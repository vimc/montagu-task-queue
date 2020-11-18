import requests


def test_run_task_through_flower():
    args = ["testGroup",
            "testDisease",
            "touchstone",
            "2020-11-04T12:21:15",
            "no_vaccination"]
    result = requests.post(
        "http://localhost:5555/api/task/send-task/run-diagnostic-reports",
        json={"args": args}
    )
    assert result.status_code == 200
    assert result.json()["task-id"] > ""
    assert result.json()["state"] == "PENDING"
