import os

from YTClient.YTDataClasses import Project, Command

from src.utils.run_reports import run_reports
from datetime import datetime, timedelta
from .celery import app
from .config import Config, ReportConfig
from src.utils.email import send_email, Emailer
from urllib.parse import quote as urlencode
import logging
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper
from src.utils.running_reports_repository import RunningReportsRepository
from YTClient.YTClient import YTClient

vimc_project_id = "78-0"


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
        yt_token = config.youtrack_token
        if yt_token is None or yt_token == "None":
            # allow yt token passed as env var when running locally
            # or during CI tests
            yt_token = os.environ["YOUTRACK_TOKEN"]
        yt = YTClient('https://mrc-ide.myjetbrains.com/youtrack/',
                      token=yt_token)

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
            create_ticket(group, disease, touchstone,
                          report, version, yt, config)

        running_reports_repo = RunningReportsRepository(host=config.host)

        return run_reports(wrapper,
                           group,
                           disease,
                           touchstone,
                           config,
                           reports,
                           success_callback,
                           running_reports_repo)
    else:
        msg = "No configured diagnostic reports for group {}, disease {}"
        logging.warning(msg.format(group, disease))
        return {}


def create_ticket(group, disease, touchstone,
                  report: ReportConfig, version,
                  yt: YTClient,
                  config: Config):
    try:
        issue = yt.create_issue(Project(vimc_project_id),
                                "Check & share diag report with {} ({}) {}"
                                .format(group, disease, touchstone),
                                get_version_url(report, version, config))
        yt.run_command(
            Command([issue], "Assignee {}".format(report.assignee)))
        yt.run_command(
            Command([issue], "tag {}".format(group)))
        yt.run_command(
            Command([issue], "tag {}".format(disease)))
        yt.run_command(
            Command([issue], "tag {}".format(touchstone)))
    except Exception as ex:
        logging.exception(ex)


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
    template_values = {
        "report_version_url": get_version_url(report, version, config),
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


def get_version_url(report, version, config):
    r_enc = urlencode(report.name)
    v_enc = urlencode(version)
    return "{}/report/{}/{}/".format(config.orderlyweb_url, r_enc, v_enc)
