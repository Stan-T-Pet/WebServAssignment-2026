FROM jenkins/jenkins:lts-jdk17

USER root

# Install docker CLI inside the Jenkins container.
# Jenkins connects to the host Docker engine via /var/run/docker.sock (mounted in docker-compose.yaml).
#
# Compose v2 plugin package availability varies by Debian release, so we install the official
# CLI plugin binary to ensure `docker compose` works.
ARG DOCKER_COMPOSE_VERSION=2.39.1
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    docker-cli \
    docker.io \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /usr/local/lib/docker/cli-plugins \
  && curl -fsSL -o /usr/local/lib/docker/cli-plugins/docker-compose \
    "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" \
  && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
  && docker compose version

USER jenkins
