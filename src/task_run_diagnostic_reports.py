from .celery import app
from .config import Config
import montagu
import orderlyweb_api
import logging


@app.task
def run_diagnostic_reports(group, disease):
    config = Config()
    orderly_web = auth(config)

    reports = config.diagnostic_reports(group, disease)
    keys = []
    for r in reports:
        key = orderly_web.run_report(r.name, r.parameters)
        keys.append(key)
        logging.info("Running report: {}. Key is {}".format(r.name, key))
    return keys


def auth(config):
    monty = montagu.MontaguAPI(config.montagu_url, config.montagu_user,
                               config.montagu_password)
    ow = orderlyweb_api.OrderlyWebAPI(config.orderlyweb_url, monty.token)
    return ow
