#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/../"

export AWS_ACCESS_KEY_ID=admin
export AWS_SECRET_ACCESS_KEY=password
export AWS_ENDPOINT_URL=http://localhost:9000
export AWS_DEFAULT_REGION=us-east-1

aws --no-cli-pager $@
