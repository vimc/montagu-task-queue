# montagu-task-queue

[Celery](https://docs.celeryproject.org/en/stable/) based task queue for Montagu.

The task queue consists of a broker (message queue)  to receive task requests, and one or more instances of a worker to 
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

Run the message queue and task queue as described above, then run `pytest`.

## Docker

Build the docker image for the worker with `scripts/build-docker.sh`.

Push the docker image to the public registry with `scripts/push-docker.sh`.

Run the worker inside docker with `scripts/run-docker-worker.sh`.

## Configuration

The worker expects to find a config file at `config/config.yml`. 

The Dockerfile copies `config/docker_config.yml` to `config/config.yml`.
This allows the worker running on metal to use a broker on `localhost` while the worker in docker needs to use
`montagu_mq`, the container name of the broker, to access its port. 