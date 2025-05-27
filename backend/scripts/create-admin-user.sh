#!/usr/bin/env bash
cd "$(dirname "$0")/../"

response=$(curl -s -X POST "http://localhost:8080/api/v1/auths/signup" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d "{ \"email\": \"admin@example.com\", \"password\": \"password\", \"name\": \"Admin\" }" \
  -w "\n%{http_code}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -ge 400 ]; then
    echo "HTTP Error $http_code"
    echo $body
    exit 1
fi

cat <<'EOF'
Default admin user is:

- email: admin@example.com
- password: password
- name: Admin
EOF
