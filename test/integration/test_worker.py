import celery

app = celery.Celery(broker="pyamqp://guest@localhost//", backend="rpc://")
sig = "src.task_run_diagnostic_reports.run_diagnostic_reports"


def test_run_diagnostic_reports():
    versions = app.signature(sig,
                             ["testGroup",
                              "testDisease",
                              "touchstone"]).delay().get()
    assert len(versions) == 2


def test_run_diagnostic_reports_nowait():
    app.send_task(sig, ["testGroup", "testDisease", "touchstone"])
