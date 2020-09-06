from .celery import app
from .config import Config
from src.utils.email import Emailer
import logging
import time
from urllib.parse import quote as urlencode
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper


@app.task
def run_diagnostic_reports(group, disease, *additional_recipients):
    config = Config()
    reports = config.diagnostic_reports(group, disease)
    if len(reports) > 0:
        wrapper = OrderlyWebClientWrapper(config)
        return run_reports(wrapper, config, reports, *additional_recipients)
    else:
        msg = "No configured diagnostic reports for group {}, disease {}"
        logging.warning(msg.format(group, disease))
        return {}


def publish_report(wrapper, name, version):
    try:
        logging.info("Publishing report version {}-{}".format(name, version))
        return wrapper.execute(wrapper.ow.publish_report, name, version)
    except Exception as ex:
        logging.exception(ex)
        return False


def run_reports(wrapper, config, reports, *additional_recipients):
    running_reports = {}
    new_versions = {}
    emailer = Emailer(config.smtp_host, config.smtp_port,
                      config.smtp_user, config.smtp_password)

    # Start configured reports
    for report in reports:
        try:
            key = wrapper.execute(wrapper.ow.run_report,
                                  report.name,
                                  report.parameters)

            running_reports[key] = report
            logging.info("Running report: {}. Key is {}".format(report.name,
                                                                key))
        except Exception as ex:
            logging.exception(ex)

    # Poll running reports until they complete
    report_poll_seconds = config.report_poll_seconds
    while len(running_reports.items()) > 0:
        finished = []
        keys = sorted(running_reports.keys())
        for key in keys:
            report = running_reports[key]
            try:
                result = wrapper.execute(wrapper.ow.report_status, key)
                if result.finished:
                    finished.append(key)
                    if result.success:
                        logging.info("Success for key {}. New version is {}"
                                     .format(key, result.version))

                        version = result.version
                        name = report.name
                        published = publish_report(wrapper, name, version)
                        if published:
                            logging.info(
                                "Successfully published report version {}-{}"
                                .format(name, version))
                            send_success_email(emailer,
                                               report,
                                               version,
                                               config,
                                               additional_recipients)
                        else:
                            logging.error(
                                "Failed to publish report version {}-{}"
                                .format(name, version))
                        new_versions[version] = {"published": published}
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


def send_success_email(emailer, report, version, config,
                       additional_recipients):
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

    recipients = report.success_email_recipients + list(additional_recipients)

    emailer.send(config.smtp_from, recipients,
                 report.success_email_subject, "diagnostic_report",
                 template_values)
