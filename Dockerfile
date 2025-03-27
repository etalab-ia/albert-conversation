# syntax=docker/dockerfile:1

# Build arguments for controlling configurations
ARG USE_CUDA=false
ARG USE_OLLAMA=false
ARG USE_CUDA_VER=cu121  # Tested with CUDA 11 (cu117) and CUDA 12 (cu121)
ARG USE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ARG USE_RERANKING_MODEL=""
ARG USE_TIKTOKEN_ENCODING_NAME="cl100k_base"
ARG BUILD_HASH=dev-build
ARG UID=0
ARG GID=0

######## WebUI: Build Frontend ########
FROM --platform=$BUILDPLATFORM node:22-alpine3.20 AS build

# Pass build hash to the environment
ARG BUILD_HASH

WORKDIR /app

# Install dependencies and build the frontend
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ENV APP_BUILD_HASH=${BUILD_HASH}
ENV NODE_ENV=production
ENV VITE_DISABLE_SOURCEMAPS=true
RUN npm run build

######## WebUI: Backend Python App ########
FROM python:3.11-slim-bookworm AS base

# Build arguments for configuring runtime
ARG USE_CUDA
ARG USE_OLLAMA
ARG USE_CUDA_VER
ARG USE_EMBEDDING_MODEL
ARG USE_RERANKING_MODEL
ARG UID
ARG GID

# Configure environment variables
ENV ENV=prod \
    PORT=8080 \
    USE_OLLAMA_DOCKER=${USE_OLLAMA} \
    USE_CUDA_DOCKER=${USE_CUDA} \
    USE_CUDA_DOCKER_VER=${USE_CUDA_VER} \
    USE_EMBEDDING_MODEL_DOCKER=${USE_EMBEDDING_MODEL} \
    USE_RERANKING_MODEL_DOCKER=${USE_RERANKING_MODEL} \
    WHISPER_MODEL="base" \
    WHISPER_MODEL_DIR="/app/backend/data/cache/whisper/models" \
    RAG_EMBEDDING_MODEL="$USE_EMBEDDING_MODEL_DOCKER" \
    RAG_RERANKING_MODEL="$USE_RERANKING_MODEL_DOCKER" \
    SENTENCE_TRANSFORMERS_HOME="/app/backend/data/cache/embedding/models" \
    TIKTOKEN_ENCODING_NAME="cl100k_base" \
    TIKTOKEN_CACHE_DIR="/app/backend/data/cache/tiktoken" \
    HF_HOME="/app/backend/data/cache/embedding/models" \
    SCARF_NO_ANALYTICS=true \
    DO_NOT_TRACK=true \
    ANONYMIZED_TELEMETRY=false \
    HOME=/root

# Create user/group (if non-root is configured in args)
RUN if [ $UID -ne 0 ]; then \
      if [ $GID -ne 0 ]; then \
        addgroup --gid $GID app; \
      fi; \
      adduser --uid $UID --gid $GID --home $HOME --disabled-password --no-create-home app; \
    fi

# Pre-create cache directories for models and set ownership
RUN mkdir -p /app/backend/data/cache/embedding/models \
             /app/backend/data/cache/whisper/models \
             /app/backend/data/cache/tiktoken && \
    chown -R $UID:$GID /app/backend/data

# Install OS-level dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
      git build-essential netcat-openbsd curl jq gcc python3-dev ffmpeg libsm6 libxext6 && \
    if [ "$USE_OLLAMA" = "true" ]; then \
      curl -fsSL https://ollama.com/install.sh | sh; \
    fi && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies (split for easier debugging)
COPY --chown=$UID:$GID ./backend/requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir uv \
    && if [ "$USE_CUDA" = "true" ]; then \
         pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/${USE_CUDA_VER} --no-cache-dir; \
       else \
         pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu --no-cache-dir; \
       fi \
    && pip3 install --no-cache-dir --system -r requirements.txt

# Preload sentence-transformers and Whisper models
RUN python3 -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('${USE_EMBEDDING_MODEL}', device='cpu')" && \
    python3 -c "from faster_whisper import WhisperModel; \
    WhisperModel('base', device='cpu', compute_type='int8', \
    download_root='/app/backend/data/cache/whisper/models')" && \
    python3 -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"

# Copy built frontend assets
COPY --chown=$UID:$GID --from=build /app/dist /app/dist
COPY --chown=$UID:$GID ./backend .

# Healthcheck
HEALTHCHECK CMD curl --silent --fail http://localhost:${PORT:-8080}/health || exit 1

# Final permissions
RUN chown -R $UID:$GID /app/backend

# Run backend code as non-root user (if configured)
USER $UID:$GID

# Expose runtime arguments and port
ARG BUILD_HASH
ENV WEBUI_BUILD_VERSION=${BUILD_HASH}
ENV DOCKER=true

EXPOSE 8080

# Launch application
CMD ["bash", "start.sh"]
