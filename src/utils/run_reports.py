import logging
import time
from enum import Enum

class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"
    DIED = "DIED"
    TIMEOUT = "TIMEOUT"
    IMPOSSIBLE = "IMPOSSIBLE"
    DEFERRED = "DEFERRED"
    MOVED = "MOVED"

def task_is_finished(poll_response):
    return poll_response.status not in [
        TaskStatus.PENDING,
        TaskStatus.RUNNING
        ]

def publish_report(wrapper, name, packet_id, roles):
    try:
        logging.info(f"Publishing report packet {name}({packet_id})")
        return packit.publish(packet_id, roles)
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

    # Start configured reports
    for report in reports:
        # Kill any currently running task for this group/disease/report
        already_running = running_reports_repo.get(group, disease, report.name)
        if already_running is not None:
            try:
                logging.info("Killing already running task: {}. Key is {}"
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
            logging.info("Running report: {} with parameters {}. Key is {}. "
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
                    if result.status == TaskStatus.COMPLETE:
                        logging.info("Success for key {}. New packet id is {}"
                                     .format(key, result.packetId))

                        packet_id = result.packetId
                        name = report.name

                        report_config = filter(lambda report: report.name == name, reports)
                        if len(report_config) > 0 and len(report_config[0].publish_roles > 0):
                            published = publish_report(wrapper, name, packet_id, report_config[0].publish_roles)
                            if published:
                                logging.info(
                                    f"Successfully published report packet {name} ({packet_id})"
                                 )
                                success_callback(report, packet_id)
                            else:
                                error = f"Failed to publish report packet {name} ({packet_id})"
                                logging.error(error)
                                error_callback(report, error)
                        new_packets[packet_id] = {
                            "published": published,
                            "report": name
                        }
                    else:
                        error = "Failure for key {}. Status: {}"\
                            .format(key, result.status)
                        logging.error(error)
                        # don't invoke error callback for cancelled runs
                        if result.status != TaskStatus.CANCELLED:
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

    return new_packet
