#!/usr/bin/env bash
set -ex

HERE=$(readlink -f "$(dirname $0)")
. $HERE/common.sh


ARCHIVE_DIR=test_archive_files
LOCAL_ARCHIVE_DIR=$HERE/../$ARCHIVE_DIR

rm $LOCAL_ARCHIVE_DIR -rf
mkdir $LOCAL_ARCHIVE_DIR


docker run --env YOUTRACK_TOKEN=$YOUTRACK_TOKEN \
    --name $NAME \
    --network=montagu_default \
    -v $LOCAL_ARCHIVE_DIR:/home/worker/src/$ARCHIVE_DIR:Z \
    -d $BRANCH_TAG

