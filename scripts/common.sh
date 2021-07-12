PACKAGE_ROOT=$(readlink -f $(dirname $0)/..)
GIT_ID=$(git -C "$PACKAGE_ROOT" rev-parse --short=7 HEAD)

GIT_BRANCH=$(git -C "$PACKAGE_ROOT" symbolic-ref --short HEAD)

REGISTRY=vimc
NAME=task-queue-worker

COMMIT_TAG=$REGISTRY/$NAME:$GIT_ID
BRANCH_TAG=$REGISTRY/$NAME:$GIT_BRANCH
