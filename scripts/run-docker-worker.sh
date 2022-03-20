#!/usr/bin/env bash
set -ex

HERE=$(readlink -f "$(dirname $0)")
. $HERE/common.sh

docker volume create files_to_archive

docker run --env YOUTRACK_TOKEN=$YOUTRACK_TOKEN \
    --name $NAME \
    --network=montagu_default \
    -d $BRANCH_TAG
    -v files_to_archive:/files_to_archive
