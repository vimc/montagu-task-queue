from .celery import app
from .config import Config
import logging
import os
import time


@app.task(name="archive_folder_contents")
def archive_folder_contents(folder_path):
    logging.info("Removing contents of {}:".format(folder_path))
    config = Config()

    min_file_age = config.archive_folder_contents.min_file_age_seconds
    now = time.time()

    for file in os.scandir(folder_path):
        logging.info(file.path)
        try:
            # only archive files which are older than min configured age
            created_time = os.path.getctime(file.path)  # s since epoch

            file_age = now - created_time

            if file_age < min_file_age:
                logging.info("Not removing {} as it is only {} seconds old".format(file.path, int(file_age)))
            else:
                os.remove(file.path)
        except Exception as ex:
            logging.exception(ex)

