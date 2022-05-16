from celery import Celery
from .config import Config
from src.task_archive_folder_contents import archive_folder_contents

config = Config()
redis_db = "redis://{}/0".format(config.host)

app = Celery('tasks',
             broker=redis_db,
             backend=redis_db,
             include=[
                 'src.task_run_diagnostic_reports',
                 'src.task_archive_folder_contents'
             ])


# Optional configuration, see the celery application user guide.
app.conf.update(
    result_expires=3600,
    timezone='Europe/London'
)


@app.on_after_configure.connect
def setup_periodic_tasks(sender):
    sender.add_periodic_task(
        crontab(hour=1),
        archive_folder_contents.s('burden_estimate_files')
    )


if __name__ == '__main__':
    app.start()
