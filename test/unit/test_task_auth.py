from src.task_auth import auth


def test_auth():
    token = auth()
    assert len(token) > 0
