#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../"

curl -X GET "https://openrouter.ai/api/v1/auth/key" \
  -H "Authorization: Bearer $OPENROUTER_API_SECRET_KEY"
