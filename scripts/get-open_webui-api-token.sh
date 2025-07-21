#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../"

curl -s -X POST http://localhost:8080/api/v1/auths/signin \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"admin@example.com\",
    \"password\": \"password\"
  }" | jq -r .token
