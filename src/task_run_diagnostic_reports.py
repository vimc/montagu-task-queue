from src.utils.run_reports import run_reports
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
        "touchstone": touchstone
    }

    send_email(emailer,
               report,
               "diagnostic_report",
               template_values,
               config,
               list(additional_recipients))
