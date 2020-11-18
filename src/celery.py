from celery import Celery
from .config import Config

config = Config()
redis_db = "redis://guest@{}/0".format(config.host)
app = Celery('tasks',
             broker=redis_db,
             backend=redis_db,
             include=['src.task_run_diagnostic_reports'])


# Optional configuration, see the celery application user guide.
app.conf.update(
    result_expires=3600,
)


if __name__ == '__main__':
    app.start()
