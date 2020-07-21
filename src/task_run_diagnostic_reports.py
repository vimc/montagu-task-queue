from .celery import app
from .config import Config
from src.utils.email import Emailer
import montagu
import orderlyweb_api
import logging
import time
from urllib.parse import quote as urlencode


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
    running_reports = {}
    new_versions = []

    # Start configured reports
    for report in reports:
        try:
            key = orderly_web.run_report(report.name, report.parameters)
            running_reports[key] = report
            logging.info("Running report: {}. Key is {}".format(report.name, key))
        except Exception as ex:
            logging.exception(ex)

    # Poll running reports until they complete
    report_poll_seconds = config.report_poll_seconds
    while len(running_reports.items()) > 0:
        finished = []
        for (key, report) in running_reports.items():
            try:
                result = orderly_web.report_status(key)
                if result.finished:
                    finished.append(key)
                    if result.success:
                        new_versions.append(result.version)
                        logging.info("Success for key {}. New version is {}"
                                     .format(key, result.version))

                        send_success_emails(report, result.version, config)
                    else:
                        logging.error("Failure for key {}.".format(key))

            except Exception as ex:
                if key not in finished:
                    finished.append(key)
                logging.exception(ex)

        for key in finished:
            running_reports.pop(key)
        time.sleep(report_poll_seconds)

    return new_versions


def send_success_emails(report, version, config):
    emailer = Emailer(config.smtp_host, config.smtp_port)

    r_enc = urlencode(report.name)
    v_enc = urlencode(version)
    version_url = "{}/report/{}/{}/".format(config.orderlyweb_url, r_enc,
                                            v_enc)

    params_array = []
    for (k, v) in report.parameters.items():
        params_array.append("{}={}".format(k, v))
    report_params = ', '.join(params_array)

    if report_params == "":
        report_params = 'no parameters'

    template_values = {
        "report_name": report.name,
        "report_version_url": version_url,
        "report_params": report_params
    }

    emailer.send(config.smtp_from, report.sucess_email_recipients,
                 report.success_email_subject, "diagnostic_report",
                 template_values)

