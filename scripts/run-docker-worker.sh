#!/usr/bin/env bash
set -ex

HERE=$(readlink -f "$(dirname $0)")
. $HERE/common.sh

docker run --name $NAME --network=montagu_default -d $BRANCH_TAG
