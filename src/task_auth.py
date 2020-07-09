from .celery import app
from .config import Config
import montagu


@app.task
def auth():
    config = Config()
    monty = montagu.MontaguAPI(config.montagu_url, config.montagu_user, config.montagu_password)
    return monty.token
