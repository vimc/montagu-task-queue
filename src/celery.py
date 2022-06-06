from celery import Celery
from .config import Config
from celery.schedules import crontab

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
    timezone='Europe/London',
    beat_schedule={
        'nightly_archive_task': {
            'task': 'archive_folder_contents',
            'schedule': crontab(hour=10),
            'args': ['burden_estimate_files']
        }
    }
)


if __name__ == '__main__':
    app.start()
