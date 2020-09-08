from .celery import app
from .config import Config
from src.utils.email import Emailer
import logging
import time
from urllib.parse import quote as urlencode
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper


@app.task
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
                                         additional_recipients)

        return run_reports(wrapper,
                           config,
                           reports,
                           success_callback)
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


def run_reports(wrapper, config, reports, success_callback):
    running_reports = {}
    new_versions = {}

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
                            success_callback(report, version)
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


def send_email(emailer,
               report,
               template_name,
               template_values,
               config,
               additional_recipients):

    recipients = report.success_email_recipients + additional_recipients
    emailer.send(config.smtp_from, recipients,
                 report.success_email_subject, template_name,
                 template_values)
