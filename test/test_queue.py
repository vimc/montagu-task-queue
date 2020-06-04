import celery

def test_add():
    app = celery.Celery(broker="pyamqp://guest@localhost//", backend="rpc://")
    result = app.signature("src.task_add.add", [1, 2]).delay().get()
    assert result == 3
