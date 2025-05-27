#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../"

curl -s ${ALBERT_OPENAI_API_URL}/models \
  -H "Authorization: Bearer $ALBERT_OPENAI_API_KEY" | jq
