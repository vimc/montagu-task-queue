from src.utils.run_reports import run_reports
from datetime import datetime, timedelta
from .celery import app
from .config import Config
from src.utils.email import send_email, Emailer
from urllib.parse import quote as urlencode
import logging
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper


@app.task(name="run-diagnostic-reports")
def run_diagnostic_reports(group,
                           disease,
                           touchstone,
                           utc_time,  # ISO string e.g 2020-11-03T10:15:30
                           scenario,
                           *additional_recipients):

    config = Config()
    reports = config.diagnostic_reports(group, disease)
    if len(reports) > 0:
        wrapper = OrderlyWebClientWrapper(config)
        emailer = Emailer(config.smtp_host, config.smtp_port,
                          config.smtp_user, config.smtp_password)

        def success_callback(report, version):
            send_diagnostic_report_email(emailer,
                                         report,
                                         version,
                                         group,
                                         disease,
                                         touchstone,
                                         utc_time,
                                         scenario,
                                         config,
                                         *additional_recipients)

        return run_reports(wrapper,
                           config,
                           reports,
                           success_callback)
    else:
        msg = "No configured diagnostic reports for group {}, disease {}"
        logging.warning(msg.format(group, disease))
        return {}


def send_diagnostic_report_email(emailer,
                                 report,
                                 version,
                                 group,
                                 disease,
                                 touchstone,
                                 utc_time,
                                 scenario,
                                 config,
                                 *additional_recipients):
    r_enc = urlencode(report.name)
    v_enc = urlencode(version)
    version_url = "{}/report/{}/{}/".format(config.orderlyweb_url, r_enc,
                                            v_enc)

    template_values = {
        "report_version_url": version_url,
        "disease": disease,
        "group": group,
        "touchstone": touchstone,
        "scenario": scenario
    }
    template_values.update(get_time_strings(utc_time))

    additional_emails = list(additional_recipients) if \
        config.use_additional_recipients else []

    send_email(emailer,
               report,
               "diagnostic_report",
               template_values,
               config,
               additional_emails)


def get_time_strings(utc_time):
    utc_dt = datetime.strptime(utc_time, "%Y-%m-%dT%H:%M:%S")
    et_dt = utc_dt - timedelta(hours=5)

    friendly_format = "%a %d %b %Y %H:%M:%S"
    utc_friendly = utc_dt.strftime(friendly_format) + " UTC"
    et_friendly = et_dt.strftime(friendly_format) + " ET"
    return {
        "utc_time": utc_friendly,
        "eastern_time": et_friendly
    }
