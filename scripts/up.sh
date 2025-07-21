#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../"

docker compose -f docker-compose.sklein.yaml up -d --wait

pip install -r backend/requirements-minimal.txt

echo "Don't forget to execute \"source .envrc\" or \"direnv allow\" to refresh variable env"
