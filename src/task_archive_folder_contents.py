from .celery import app
import logging
import os


@app.task(name="archive_folder_contents")
def archive_folder_contents(folder_path):
    logging.info("Removing contents of {}:".format(folder_path))
    # TODO: Don't attempt to remove very recently created files ?
    # - but that's going to make testing tricky!
    for file in os.scandir(folder_path):
        logging.info(file.path)
        try:
            os.remove(file.path)
        except Exception as ex:
            logging.exception(ex)
