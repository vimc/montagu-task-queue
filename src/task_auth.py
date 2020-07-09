from .celery import app
import montagu


@app.task
def auth():
    monty = montagu.MontaguAPI("http://localhost:8080", "test.user@example.com", "password")
    return monty.token
