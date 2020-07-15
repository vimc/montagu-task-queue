from .celery import app
from .config import Config
import montagu
import orderlyweb_api
import logging
import time


@app.task
def run_diagnostic_reports(group, disease):
    config = Config()
    reports = config.diagnostic_reports(group, disease)
    if len(reports) > 0:
        orderly_web = auth(config)
        return run_reports(orderly_web, config, reports)
    else:
        msg = "No configured diagnostic reports for group {}, disease {}"
        logging.warning(msg.format(group, disease))
        return []


def auth(config):
    monty = montagu.MontaguAPI(config.montagu_url, config.montagu_user,
                               config.montagu_password)
    ow = orderlyweb_api.OrderlyWebAPI(config.orderlyweb_url, monty.token)
    return ow


def run_reports(orderly_web, config, reports):
    keys = []
    new_versions = []

    # Start configured reports
    for r in reports:
        try:
            key = orderly_web.run_report(r.name, r.parameters)
            keys.append(key)
            logging.info("Running report: {}. Key is {}".format(r.name, key))
        except Exception as ex:
            logging.exception(ex)

    # Poll running reports until they complete
    report_poll_seconds = config.report_poll_seconds
    while len(keys) > 0:
        finished = []
        for k in keys:
            try:
                result = orderly_web.report_status(k)
                if result.finished:
                    finished.append(k)
                    if result.success:
                        new_versions.append(result.version)
                        logging.info("Success for key {}. New version is {}"
                                     .format(k, result.version, result.output))
                    else:
                        logging.error("Failure for key {}. Status: {}"
                                      .format(k, result.status, result.output))

            except Exception as ex:
                keys.remove(k)
                logging.exception(ex)

        for k in finished:
            keys.remove(k)
        time.sleep(report_poll_seconds)

    return new_versions
