if docker compose -f docker-compose.sklein.yaml ps --services --filter "status=running" | grep -q "postgres"; then
    POSTGRES_DOCKER_ID=$(docker compose -f docker-compose.sklein.yaml ps postgres --format json | jq .ID -r)
    export POSTGRES_PORT=$(docker inspect ${POSTGRES_DOCKER_ID} | jq -r '.[].NetworkSettings.Ports["5432/tcp"][0].HostPort')
else
    unset POSTGRES_PORT
fi

if docker compose -f docker-compose.sklein.yaml ps --services --filter "status=running" | grep -q "redis"; then
    REDIS_DOCKER_ID=$(docker compose -f docker-compose.sklein.yaml ps redis --format json | jq .ID -r)
    export REDIS_PORT=$(docker inspect ${REDIS_DOCKER_ID} | jq -r '.[].NetworkSettings.Ports["6379/tcp"][0].HostPort')
else
    unset REDIS_PORT
fi

if docker compose -f docker-compose.sklein.yaml ps --services --filter "status=running" | grep -q "pipelines"; then
    PIPELINES_DOCKER_ID=$(docker compose -f docker-compose.sklein.yaml ps pipelines --format json | jq .ID -r)
    export PIPELINES_PORT=$(docker inspect ${PIPELINES_DOCKER_ID} | jq -r '.[].NetworkSettings.Ports["9099/tcp"][0].HostPort')
else
    unset PIPELINES_PORT
fi
