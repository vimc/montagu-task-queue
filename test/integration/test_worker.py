import celery

app = celery.Celery(broker="pyamqp://guest@localhost//", backend="rpc://")


def test_add_wait():
    result = app.signature("src.task_add.add", [1, 2]).delay().get()
    assert result == 3


def test_add_nowait():
    app.send_task("src.task_add.add", [2, 3])


def test_auth():
    result = app.signature("src.task_auth.auth").delay().get()
    assert len(result) > 0
