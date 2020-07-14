from .celery import app
from .config import Config
import montagu
import orderlyweb_api


@app.task
def auth():
    config = Config()
    monty = montagu.MontaguAPI(config.montagu_url, config.montagu_user,
                               config.montagu_password)
    ow = orderlyweb_api.OrderlyWebAPI(config.orderlyweb_url, monty.token)
    return ow.token
