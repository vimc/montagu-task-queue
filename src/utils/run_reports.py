import logging
import time


def publish_report(wrapper, name, version):
    try:
        logging.info("Publishing report version {}-{}".format(name, version))
        return wrapper.execute(wrapper.ow.publish_report, name, version)
    except Exception as ex:
        logging.exception(ex)
        return False


def params_to_string(params):
    return ", ".join([f"{key}={value}" for key, value in params.items()])


def run_reports(wrapper, group, disease, touchstone, config, reports, success_callback,
                running_reports_repo):
    running_reports = {}
    new_versions = {}

    if wrapper.ow is None:
        logging.error("Orderlyweb authentication failed; could not begin task")
        return new_versions

    # Start configured reports
    for report in reports:
        # Kill any currently running report for this group/disease/report
        already_running = running_reports_repo.get(group, disease, report.name)
        if already_running is not None:
            try:
                logging.info("Killing already running report: {}. Key is {}"
                             .format(report.name, already_running))
                wrapper.execute(wrapper.ow.kill_report, already_running)
            except Exception as ex:
                logging.exception(ex)

        # Assume report requires touchstone and touchstone_name parameters
        parameters = report.parameters or {}
        parameters["touchstone"] = touchstone
        parameters["touchstone_name"] = touchstone.split("-")[0]

        try:
            key = wrapper.execute(wrapper.ow.run_report,
                                  report.name,
                                  parameters,
                                  report.timeout)

            running_reports[key] = report
            # Save key to shared data - may be killed by subsequent task
            running_reports_repo.set(group, disease, report.name, key)
            logging.info("Running report: {} with parameters {}. Key is {}. Timeout is {}s."
                         .format(report.name, params_to_string(parameters), key, report.timeout))
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
                        new_versions[version] = {
                            "published": published,
                            "report": name
                        }
                    else:
                        logging.error("Failure for key {}.".format(key))

            except Exception as ex:
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

    return new_versions
