#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../"

docker compose exec redis redis-cli -n 0
