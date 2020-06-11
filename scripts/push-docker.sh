#!/usr/bin/env bash
set -ex

HERE=$(dirname $0)
. $HERE/common.sh

docker push $COMMIT_TAG \
    && docker push $BRANCH_TAG