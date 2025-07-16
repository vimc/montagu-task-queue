import logging
import time

TASK_STATUS_PENDING = "PENDING"
TASK_STATUS_RUNNING = "RUNNING"
TASK_STATUS_COMPLETE = "COMPLETE"
TASK_STATUS_CANCELLED = "CANCELLED"


def task_is_finished(poll_response):
    status = poll_response["status"]
    return status not in [
        TASK_STATUS_PENDING,
        TASK_STATUS_RUNNING
    ]


def publish_report(packit, name, packet_id, roles):
    try:
        return packit.publish(name, packet_id, roles)
    except Exception as ex:
        logging.exception(ex)
        return False


def params_to_string(params):
    return ", ".join([f"{key}={value}" for key, value in params.items()])


def run_reports(packit, group, disease, touchstone, config, reports,
                success_callback, error_callback, running_reports_repo):
    running_reports = {}
    new_packets = {}

    if not packit.auth_success:
        error = "Packit authentication failed; could not begin task"
        for report in reports:
            error_callback(report, error)
        logging.error(error)
        return new_packets

    try:
        packit.refresh_git()
    except Exception as ex:
        error = "Failed to refresh git; could not begin task"
        for report in reports:
            error_callback(report, error)
        logging.error(error)
        return new_packets

    # Start configured reports
    for report in reports:
        # Kill any currently running task for this group/disease/report
        already_running = running_reports_repo.get(group, disease, report.name)
        if already_running is not None:
            try:
                logging.info("Killing already running task: {}. Key is {}."
                             .format(report.name, already_running))
                packit.kill_task(already_running)
            except Exception as ex:
                logging.exception(ex)

        # Assume report requires touchstone and touchstone_name parameters
        parameters = report.parameters or {}
        parameters["touchstone"] = touchstone
        parameters["touchstone_name"] = touchstone.rsplit('-', 1)[0]

        try:
            key = packit.run(
                report.name,
                parameters
            )

            running_reports[key] = report
            # Save key to shared data - may be killed by subsequent task
            running_reports_repo.set(group, disease, report.name, key)
            logging.info("Running report: {} with parameters {}. Key is {}."
                         .format(report.name, params_to_string(parameters),
                                 key))
        except Exception as ex:
            error_callback(report, str(ex))
            logging.exception(ex)

    # Poll running tasks until they complete
    report_poll_seconds = config.report_poll_seconds
    while len(running_reports.items()) > 0:
        finished = []
        keys = sorted(running_reports.keys())
        for key in keys:
            report = running_reports[key]
            try:
                result = packit.poll(key)
                if task_is_finished(result):
                    finished.append(key)
                    if result["status"] == TASK_STATUS_COMPLETE:
                        logging.info("Success for key {}. New packet id is {}"
                                     .format(key, result["packetId"]))

                        packet_id = result["packetId"]
                        name = report.name

                        report_config = next(
                            filter(lambda report: report.name == name,
                                   reports),
                            None)
                        if report_config is not None:
                            logging.info(
                                "Publishing report packet {} ({})"
                                .format(name, packet_id))
                            published = publish_report(
                                packit, name, packet_id,
                                report_config.publish_roles)
                            if published:
                                logging.info(
                                    "Successfully published report packet " +
                                    f"{name} ({packet_id})"
                                )
                                success_callback(report, packet_id)
                            else:
                                error = "Failed to publish report packet " +
                                f"{name} ({packet_id})"
                                logging.error(error)
                                error_callback(report, error)
                        new_packets[packet_id] = {
                            "published": published,
                            "report": name
                        }
                    else:
                        error = "Failure for key {}. Status: {}"\
                            .format(key, result["status"])
                        logging.error(error)
                        # don't invoke error callback for cancelled runs
                        if result["status"] != TASK_STATUS_CANCELLED:
                            error_callback(report, error)

            except Exception as ex:
                error_callback(report, str(ex))
                if key not in finished:
                    finished.append(key)
                logging.exception(ex)

        for key in finished:
            report = running_reports[key]
            running_reports.pop(key)
            # delete finished report, unless it's been updated by another task
            running_reports_repo.delete_if_matches(group, disease, report.name,
                                                   key)
        time.sleep(report_poll_seconds)

    return new_packets
