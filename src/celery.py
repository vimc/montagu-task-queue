from celery import Celery

#TODO: Get these values from config
app = Celery('tasks',
             broker='pyamqp://guest@montagu_mq//',
             backend='rpc://',
             include=['src.task_add'])

# Optional configuration, see the celery application user guide.
app.conf.update(
    result_expires=3600,
)


if __name__ == '__main__':
    app.start()
