#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../"

docker compose -f docker-compose.sklein.yaml ps
