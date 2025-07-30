#!/usr/bin/env bash
set -ex

./scripts/run-dependencies.sh

# From now on, if the user presses Ctrl+C we should teardown gracefully
function cleanup() {
  docker container stop reverse-proxy
  docker container rm reverse-proxy -v
  # Same exit code issue for packit stop as packit start....
  set +e
  hatch env run -- packit stop
  set -e
  # remove db volume manually rather than --volumes flag to packit, to avoid requiring user confirmation
  docker volume rm montagu_packit_db montagu_orderly_library montagu_outpack_volume montagu_orderly_logs
  docker compose --project-name montagu down -v
}
trap cleanup EXIT

# Wait for Ctrl+C
echo "Ready to use. Press Ctrl+C to teardown."
sleep infinity