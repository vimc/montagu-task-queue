#!/usr/bin/env bash
set -ex

export REGISTRY=vimc

here=$(dirname $0)
./scripts/clear-docker.sh
docker network prune -f

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

# Run packit
hatch env run pip3 install constellation
hatch env run pip3 install packit-deploy
hatch env run packit configure $here
hatch env run -- packit start --pull

docker exec montagu-packit-db wait-for-db

# Run the proxy here, not through docker compose - it needs packit to be running before it will start up
MONTAGU_PROXY_TAG=vimc/montagu-reverse-proxy:master
docker pull $MONTAGU_PROXY_TAG
docker run -d \
  -p "443:443" -p "80:80" \
	--name reverse-proxy \
	--network montagu_default\
	$MONTAGU_PROXY_TAG 443 localhost

# give packit api some time to migrate the db...
sleep 5

# create roles to publish to...
docker exec -i montagu-packit-db psql -U packituser -d packit --single-transaction <<EOF
insert into "role" (name, is_username) values ('Funders', FALSE);
insert into "role" (name, is_username) values ('minimal.modeller', FALSE);
insert into "role" (name, is_username) values ('other.modeller', FALSE);
EOF

# Add user to packit, as admin
USERNAME='test.user'
EMAIL='test.user@example.com'
DISPLAY_NAME='Test User'
ROLE='ADMIN'
docker exec montagu-packit-db create-preauth-user --username "$USERNAME" --email "$EMAIL" --displayname "$DISPLAY_NAME" --role "$ROLE"


