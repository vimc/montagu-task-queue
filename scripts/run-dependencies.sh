#!/usr/bin/env bash
set -ex

./scripts/clear-docker.sh

docker network prune -f
docker network create nw

docker run --name montagu_mq --network=nw -d -p 5672:5672 rabbitmq