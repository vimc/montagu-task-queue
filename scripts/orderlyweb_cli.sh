#!/usr/bin/env bash

image=${REGISTRY}/orderly-web-user-cli:master
docker pull $image
docker run --rm -v orderly_volume:/orderly --network ${NETWORK} $image $@