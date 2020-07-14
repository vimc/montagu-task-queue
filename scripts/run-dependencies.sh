#!/usr/bin/env bash
set -ex

here=$(dirname $0)

./scripts/clear-docker.sh
docker network prune -f

export REGISTRY=vimc
export NETWORK=montagu_default

# Run the API and database
docker-compose pull
docker-compose --project-name montagu up -d

# Install orderly-web
pip3 install orderly-web
orderly-web start $here

#orderly:
#    image: ${REGISTRY}/orderly.server:master
#    ports:
#      - "8321:8321"
#    volumes:
#      - orderly_volume:/orderly
#    command: --port 8321 --go-signal /orderly_go /orderly
#  orderly_web:
#    image: ${REGISTRY}/orderly-web:master
#    ports:
#      - "8888:8888"
#    depends_on:
#      - api
#    volumes:
#      - orderly_volume:/orderly
#volumes:
#  orderly_volume:



# Start the APIs
docker exec montagu_api_1 mkdir -p /etc/montagu/api/
docker exec montagu_api_1 touch /etc/montagu/api/go_signal

# Wait for the database
docker exec montagu_db_1 montagu-wait.sh

# migrate the database
migrate_image=${REGISTRY}/montagu-migrate:master
docker pull $migrate_image
docker run --network=${NETWORK} $migrate_image

# add test user
$here/montagu_cli.sh add "Test User" test.user \
    test.user@example.com password \
    --if-not-exists

$here/montagu_cli.sh addRole test.user user

# generate report test database
#rm demo -rf
#rm git -rf
#orderly_data_image=${REGISTRY}/orderly:master
#docker pull $orderly_data_image
#docker run --rm \
#  --entrypoint create_orderly_demo.sh \
#  -u $UID \
#  -v $PWD:/orderly \
#  -w "/orderly" \
#  $orderly_data_image \
#  "."

# Copy the demo orderly files to top level
#docker cp $PWD/demo/. montagu_orderly_1:/orderly

# Migrate the orderlyweb tables
#ow_migrate_image=$REGISTRY/orderlyweb-migrate:master
#docker pull $ow_migrate_image
#docker run --rm --network=${NETWORK} \
#  -v montagu_orderly_volume:/orderly \
#  $ow_migrate_image

# Add user to orderlyweb
$here/orderlyweb_cli.sh add-users test.user@example.com
$here/orderlyweb_cli.sh grant test.user@example.com */reports.run

# start orderly
#docker exec montagu_orderly_1 mkdir -p /orderly_go
#docker exec montagu_orderly_1 touch /orderly_go/go_signal

# Copy orderlyweb config properties
#docker exec montagu_orderly_web_1 mkdir -p /etc/orderly/web
#docker cp $here/config.properties montagu_orderly_web_1:/etc/orderly/web

# start orderlyweb
#docker exec montagu_orderly_web_1 touch /etc/orderly/web/go_signal