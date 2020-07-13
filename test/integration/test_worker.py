import celery

app = celery.Celery(broker="pyamqp://guest@localhost//", backend="rpc://")


def test_add_wait():
    result = app.signature("src.task_add.add", [1, 2]).delay().get()
    assert result == 3


def test_add_nowait():
    app.send_task("src.task_add.add", [2, 3])


def test_run_diagnostic_reports():
    sig = "src.task_run_diagnostic_reports.run_diagnostic_reports"
    versions = app.signature(sig, ["testGroup", "testDisease"]).delay().get()
    assert len(versions) == 2
