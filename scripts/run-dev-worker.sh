#!/usr/bin/env bash
set -ex

celery -A src worker -l info