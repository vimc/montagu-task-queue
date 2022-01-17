import json
import urllib.parse
import os

from YTClient.YTDataClasses import Project, Command, Issue
from YTClient.RequestEngine import RequestType, RequestEngine

from src.utils.run_reports import run_reports
from datetime import datetime, timedelta
from .celery import app
from .config import Config, ReportConfig
from src.utils.email import send_email, Emailer
from urllib.parse import quote as urlencode
import logging
from src.orderlyweb_client_wrapper import OrderlyWebClientWrapper
from src.utils.running_reports_repository import RunningReportsRepository
from YTClient.YTClient import YTClient, YTException

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
                          report, version, None, yt, config)

        def error_callback(report, error):
            create_ticket(group, disease, touchstone,
                          report, None, error, yt, config)

        running_reports_repo = RunningReportsRepository(host=config.host)

        return run_reports(wrapper,
                           group,
                           disease,
                           touchstone,
                           config,
                           reports,
                           success_callback,
                           error_callback,
                           running_reports_repo)
    else:
        msg = "No configured diagnostic reports for group {}, disease {}"
        logging.warning(msg.format(group, disease))
        return {}


def create_ticket(group, disease, touchstone,
                  report: ReportConfig, version,
                  error,
                  yt: YTClient,
                  config: Config):
    try:
        report_success = version is not None
        summary = "Check & share diag report with {} ({}) {}" if \
            report_success else \
            "Run, check & share diag report with {} ({}) {}"
        description = get_version_url(report, version, config) if \
            report_success else \
            "Auto-run failed with error: {}".format(error)
        create_tags(yt, group, disease, touchstone, report)
        query = "tag: {} AND tag: {} AND tag: {} AND tag: {} " \
                "AND state: Incoming"
        existing_issues = yt.get_issues(
            query.format(disease, touchstone, group, report.name),
            ["id", "summary", "description", "tags(name)"])
        summary = summary.format(group, disease, touchstone)
        if len(existing_issues) > 0:
            existing_issue = existing_issues[0]
            yt.update_issue(existing_issue, summary, description)
        else:
            issue = yt.create_issue(Project(vimc_project_id),
                                    summary,
                                    description)
            comm = "for {} implementer {} tag {} tag {} tag {} tag {}".format(
                report.assignee,
                report.assignee,
                group, disease,
                touchstone,
                report.name)
            yt.run_command(
                Command([issue], comm))
    except Exception as ex:
        logging.exception(ex)


def create_tags(yt, group, disease, touchstone, report):
    tags = yt.get_tags(fields=["name"])
    if len([t for t in tags if t["name"] == disease]) == 0:
        yt.create_tag(disease)
    if len([t for t in tags if t["name"] == group]) == 0:
        yt.create_tag(group)
    if len([t for t in tags if t["name"] == touchstone]) == 0:
        yt.create_tag(touchstone)
    if len([t for t in tags if t["name"] == report.name]) == 0:
        yt.create_tag(report.name)


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
