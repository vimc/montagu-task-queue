PACKAGE_ROOT=$(readlink -f $(dirname $0)/..)
GIT_ID=$(git -C "$PACKAGE_ROOT" rev-parse --short=7 HEAD)

if [ -z "$TRAVIS_BRANCH" ]; then
    GIT_BRANCH=$(git -C "$PACKAGE_ROOT" symbolic-ref --short HEAD)
else
    GIT_BRANCH=$TRAVIS_BRANCH
fi

REGISTRY=vimc
NAME=task-queue-worker

COMMIT_TAG=$REGISTRY/$NAME:$GIT_ID
BRANCH_TAG=$REGISTRY/$NAME:$GIT_BRANCH
