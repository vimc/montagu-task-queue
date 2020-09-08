from src.utils.run_reports import run_reports
from .celery import app
from .config import Config
from src.utils.email import send_email, Emailer
import logging
from urllib.parse import quote as urlencode
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper


@app.task
def run_diagnostic_reports(group, disease, *additional_recipients):
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
                                         config,
                                         *additional_recipients)
        return run_reports(wrapper, config, reports, success_callback)
    else:
        msg = "No configured diagnostic reports for group {}, disease {}"
        logging.warning(msg.format(group, disease))
        return {}


def send_diagnostic_report_email(emailer, report, version, config,
                                 *additional_recipients):
    r_enc = urlencode(report.name)
    v_enc = urlencode(version)
    version_url = "{}/report/{}/{}/".format(config.orderlyweb_url, r_enc,
                                            v_enc)

    report_params = 'no parameters'
    if report.parameters is not None and len(report.parameters.items()) > 0:
        params_array = []
        for (k, v) in report.parameters.items():
            params_array.append("{}={}".format(k, v))
        report_params = ', '.join(params_array)

    template_values = {
        "report_name": report.name,
        "report_version_url": version_url,
        "report_params": report_params
    }

    send_email(emailer,
               report,
               "diagnostic_report",
               template_values,
               config,
               list(additional_recipients))
