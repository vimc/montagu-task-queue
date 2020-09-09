import logging
import time


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

    if wrapper.ow is None:
        logging.error("Orderlyweb authentication failed; could not begin task")
        return new_versions

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
