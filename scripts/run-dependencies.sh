#!/usr/bin/env bash
set -ex

here=$(dirname $0)

./scripts/clear-docker.sh
docker network prune -f

export REGISTRY=vimc
export NETWORK=montagu_default

# Run the API and database
docker compose pull
docker compose --project-name montagu up -d

# Clear redis
docker exec montagu-mq-1 redis-cli FLUSHALL

# Start the APIs
docker exec montagu-api-1 mkdir -p /etc/montagu/api/
docker exec montagu-api-1 touch /etc/montagu/api/go_signal

# Wait for the database
docker exec montagu-db-1 montagu-wait.sh

# migrate the database
migrate_image=${REGISTRY}/montagu-migrate:master
docker pull $migrate_image
docker run --network=${NETWORK} $migrate_image

# add test user
$here/montagu_cli.sh add "Test User" test.user \
    test.user@example.com password \
    --if-not-exists

$here/montagu_cli.sh addRole test.user user

# TODO: Add user to Packit
# Add user to orderlyweb
#$here/orderlyweb_cli.sh add-users test.user@example.com
#$here/orderlyweb_cli.sh grant test.user@example.com */reports.read */reports.run */reports.review
