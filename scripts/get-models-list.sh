#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../"

API_TOKEN="$(./scripts/get-open_webui-api-token.sh)"

curl -s -X 'GET' \
  'http://localhost:8080/openai/models' \
  -H 'accept: application/json' \
  -H "Authorization: Bearer ${API_TOKEN}" | jq .data[].name
