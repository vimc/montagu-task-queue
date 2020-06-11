from celery import Celery
from .config import Config

config = Config()
app = Celery('tasks',
             broker=config.broker,
             backend=config.backend,
             include=['src.task_add'])


# Optional configuration, see the celery application user guide.
app.conf.update(
    result_expires=3600,
)


if __name__ == '__main__':
    app.start()
