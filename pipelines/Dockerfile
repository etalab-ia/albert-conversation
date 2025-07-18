# Open WebUI Pipelines version from 2025-04-14
# https://github.com/open-webui/pipelines/pkgs/container/pipelines/395282396?tag=git-7f9f957
FROM ghcr.io/open-webui/pipelines:git-7f9f957

COPY ./requirements-openwebui-pipelines.txt /app/requirements-custom.txt

RUN pip install -r /app/requirements-custom.txt
