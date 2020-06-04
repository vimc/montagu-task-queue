# montagu-task-queue

[Celery](https://docs.celeryproject.org/en/stable/) based task queue for Montagu

## Installation

Clone the repo anywhere and install dependencies with (from the repo root):

```
pip3 install --user -r requirements.txt
```

## Development

Run the message queue dependency in docker with `scripts/run-dev-mq.sh`

Run the task queue with `scripts/run-task-queue.sh`

## Testing

Run the message queue and task queue as described above, then run `pytest`