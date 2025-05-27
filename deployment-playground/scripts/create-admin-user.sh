#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../"

curl \
  -X POST "http://localhost:8080/api/v1/auths/signup" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{ \"email\": \"admin@example.com\", \"password\": \"password\", \"name\": \"Admin\" }"
