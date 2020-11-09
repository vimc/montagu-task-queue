import celery

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
