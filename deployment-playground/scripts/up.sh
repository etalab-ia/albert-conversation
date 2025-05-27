#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../"

./scripts/create-minio-bucket.sh
docker compose up -d --wait
./scripts/create-admin-user.sh
