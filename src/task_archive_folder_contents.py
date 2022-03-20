from .celery import app
import logging
import os

@app.task(name="archive_folder_contents")
def archive_folder_contents(folder_path):
    logging.info("Removing contents of {}:".format(folder_path))
    for file in os.scandir(dir):
        logging.info(file.path)
        os.remove(file.path)

