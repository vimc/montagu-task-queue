#!/usr/bin/env bash

image=vimc/montagu-cli:master
docker pull $image
exec docker run --rm --network montagu_default $image "$@"