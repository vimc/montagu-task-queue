# montagu-task-queue

[![build](https://github.com/vimc/montagu-task-queue/actions/workflows/test-and-push.yml/badge.svg)](https://github.com/vimc/montagu-task-queue/actions/workflows/test-and-push.yml)
[![codecov.io](https://codecov.io/github/vimc/montagu-task-queue/coverage.svg?branch=master)](https://codecov.io/github/vimc/montagu-task-queue?branch=master)

[Celery](https://docs.celeryproject.org/en/stable/) based task queue for Montagu.

The task queue consists of a broker (message queue)  to receive task requests, and one or more instances of a worker to 
execute tasks, coordinated by Celery. Celery supports various message brokers including RabbitMQ and Redis.

## Installation

Clone the repo anywhere and install dependencies with (from the repo root):

```
pip3 install --user -r requirements.txt
```

## Development

Run dependencies (Montagu API and DB, OrderlyWeb and a local Redis message queue in docker) with `scripts/run-dependencies.sh`

Dependencies also include a fake smtp server run from a [docker image](https://hub.docker.com/r/reachfive/fake-smtp-server)
to enable development and testing of email functionality. You can see a web front end for the emails 'sent' via this server
at http://localhost:1080 and an API at http://localhost:1080/api/emails

Run a worker with `scripts/run-dev-worker.sh`. You can `Ctrl-C` out of this process to terminate the worker. 

If you end 
up with an old worker still running (which causes new workers to complain that another node is already listening), you
kill all dev workers with `pkill -9 -f 'celery -A src worker'`.

YouTrack tickets will be created if you have an environment variable `YOUTRACK_TOKEN` in your environment with a valid 
YouTrack permanent API token.

## Testing

Run the dependencies and task queue as described above, then run `pytest`.

## Docker

Build the docker image for the worker with `scripts/build-docker.sh`.

Push the docker image to the public registry with `scripts/push-docker.sh`.

Run the worker inside docker with `scripts/run-docker-worker.sh`.

You can test that the docker image is working by running `pytest` as described as above, with the worker running inside
docker instead of using the `run-dev-worker.sh` script.

## Configuration

The worker expects to find a config file at `config/config.yml`. 

The Dockerfile copies `config/docker_config.yml` to `config/config.yml`.
This allows the worker running on metal to use a broker on `localhost` while the worker in docker needs to use
`montagu_mq`, the container name of the broker, to access its port. 

Note that if a YouTrack token is not provided in the config the app will look for an environment variable called `YOUTRACK_TOKEN`. 
This makes local and automated testing of the YouTrack integration possible. 
During `montagu` deployment a token from the vault will be added to the config.
