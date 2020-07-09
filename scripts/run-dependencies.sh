#!/usr/bin/env bash
set -ex

./scripts/clear-docker.sh
docker network prune -f

#Run the API and database
docker-compose pull
docker-compose --project-name montagu up -d

# Start the APIs
docker exec montagu_api_1 mkdir -p /etc/montagu/api/
docker exec montagu_api_1 touch /etc/montagu/api/go_signal

# Wait for the database
docker exec montagu_db_1 montagu-wait.sh

# migrate the database
migrate_image=vimc/montagu-migrate:master
docker pull $migrate_image
docker run --network=montagu_default $migrate_image

# add test user
here=$(dirname $0)

$here/montagu_cli.sh add "Test User" test.user \
    test.user@example.com password \
    --if-not-exists

$here/montagu_cli.sh addRole test.user user