# montagu-task-queue

[Celery](https://docs.celeryproject.org/en/stable/) based task queue for Montagu.

The task queue consists of a message queue or broker  to receive task requests, and one or more instances of a worker to 
execute tasks, coordinated by Celery. Celery supports various message brokers including RabbitMQ and Redis.

## Installation

Clone the repo anywhere and install dependencies with (from the repo root):

```
pip3 install --user -r requirements.txt
```

## Development

Run dependencies (a local RabbitMQ message queue in docker) with `scripts/run-dependencies.sh`

Run a worker with `scripts/run-dev-worker.sh`

## Testing

Run the message queue and task queue as described above, then run `pytest`