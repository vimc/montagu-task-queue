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
# For some reason packit is emitting exit code 1 despite apparently succeeding. Allow this for now...
set +e
hatch env run -- packit start --pull $here
echo Packit deployed with exit code $?
set -e

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
sleep 10

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

# From now on, if the user presses Ctrl+C we should teardown gracefully
function cleanup() {
  docker container stop reverse-proxy
  docker container rm reverse-proxy -v
  # Same exit code issue for packit stop as packit start....
  set +e
  hatch env run -- packit stop ./scripts
  set -e
  # remove db volume manually rather than --volumes flag to packit, to avoid requiring user confirmation
  docker volume rm montagu_packit_db montagu_orderly_library montagu_outpack_volume montagu_orderly_logs
  docker compose --project-name montagu down -v
}
trap cleanup EXIT

# Wait for Ctrl+C
echo "Ready to use. Press Ctrl+C to teardown."
sleep infinity
