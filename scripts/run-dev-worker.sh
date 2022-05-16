#!/usr/bin/env bash
set -ex

# Run worker with beat scheduler
celery -A src worker -l INFO -B