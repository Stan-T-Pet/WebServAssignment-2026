pipeline {
  agent any

  options {
    timestamps()
  }

  stages {
    stage('Pull From GitHub') {
      steps {
        git branch: 'main', url: 'https://github.com/Stan-T-Pet/WebServAssignment-2026.git'
      }
    }

    stage('Build and Run Ubuntu Container in Background') {
      steps {
        sh '''
          set -eux

          NETWORK="ci-${BUILD_NUMBER}"
          MONGO_NAME="mongo-ci-${BUILD_NUMBER}"
          API_NAME="api-ci-${BUILD_NUMBER}"
          API_IMAGE="api-ubuntu:${BUILD_NUMBER}"

          # Fresh network for this build
          docker network rm "$NETWORK" >/dev/null 2>&1 || true
          docker network create "$NETWORK"

          # Start MongoDB (background)
          docker rm -f "$MONGO_NAME" >/dev/null 2>&1 || true
          docker run -d --name "$MONGO_NAME" --network "$NETWORK" \
            -e MONGO_INITDB_ROOT_USERNAME=admin \
            -e MONGO_INITDB_ROOT_PASSWORD=adminPassword123 \
            mongo:latest

          # Build an Ubuntu-based image for the API (contains the code pulled from GitHub)
          docker build -t "$API_IMAGE" -f Dockerfile .

          # Run Python unit tests inside the Ubuntu container image
          docker run --rm "$API_IMAGE" python3 -m pytest -q

          # Seed Mongo with products.json
          for i in $(seq 1 20); do
            if docker run --rm --network "$NETWORK" \
              -e MONGO_URI="mongodb://admin:adminPassword123@${MONGO_NAME}:27017/?authSource=admin" \
              -e MONGO_DB="inventory_db" \
              "$API_IMAGE" \
              python3 seed_mongo.py; then
              echo "MongoDB seeded"
              break
            fi
            sleep 2
          done

          # Start API (background)
          docker rm -f "$API_NAME" >/dev/null 2>&1 || true
          docker run -d --name "$API_NAME" --network "$NETWORK" \
            -e MONGO_URI="mongodb://admin:adminPassword123@${MONGO_NAME}:27017/?authSource=admin" \
            -e MONGO_DB="inventory_db" \
            -e EXCHANGE_RATE_API_KEY="${EXCHANGE_RATE_API_KEY:-}" \
            "$API_IMAGE"

          # Wait until the API is reachable
          for i in $(seq 1 60); do
            if docker run --rm --network "$NETWORK" curlimages/curl:8.7.1 -fsS "http://${API_NAME}:8000/" >/dev/null; then
              echo "API is up"
              exit 0
            fi
            sleep 2
          done

          echo "API did not become ready in time"
          docker logs "$API_NAME" || true
          exit 1
        '''
      }
    }

    stage('Run Postman Tests (Newman)') {
      steps {
        sh '''
          set -eux

          NETWORK="ci-${BUILD_NUMBER}"
          API_NAME="api-ci-${BUILD_NUMBER}"
          NEWMAN_NAME="newman-ci-${BUILD_NUMBER}"

          docker rm -f "$NEWMAN_NAME" >/dev/null 2>&1 || true

          # Avoid mounting $WORKSPACE (paths are interpreted on the Docker host). Use docker cp instead.
          docker create --name "$NEWMAN_NAME" --network "$NETWORK" postman/newman:alpine \
            run /etc/newman/collection.json \
            --env-var baseUrl="http://${API_NAME}:8000" \
            -r cli,junit \
            --reporter-junit-export /etc/newman/newman-report.xml

          docker cp postman/InventoryAPI.postman_collection.json "$NEWMAN_NAME:/etc/newman/collection.json"
          docker start -a "$NEWMAN_NAME"
          docker cp "$NEWMAN_NAME:/etc/newman/newman-report.xml" newman-report.xml
          docker rm -f "$NEWMAN_NAME" >/dev/null 2>&1 || true
        '''
      }
    }

    stage('Generate README.txt + Zip Artifact') {
      steps {
        sh '''
          set -eux

          NETWORK="ci-${BUILD_NUMBER}"
          API_NAME="api-ci-${BUILD_NUMBER}"
          API_IMAGE="api-ubuntu:${BUILD_NUMBER}"
          ZIP_NAME="zip-ci-${BUILD_NUMBER}"

          # Generate README.txt from FastAPI OpenAPI output
            docker run --rm --network "$NETWORK" \
            -e API_BASE_URL="http://${API_NAME}:8000" \
            "$API_IMAGE" \
            python3 - <<'PY' > README.txt
      import os
      import json
      import urllib.request

      base = os.environ["API_BASE_URL"].rstrip("/")
      openapi_url = base + "/openapi.json"
      docs_url = base + "/docs"

      with urllib.request.urlopen(openapi_url, timeout=20) as resp:
        spec = json.loads(resp.read().decode("utf-8"))

      lines = []
      lines.append("Inventory API - Endpoints\n")
      lines.append(f"OpenAPI JSON: {openapi_url}\n")
      lines.append(f"Swagger UI (FastAPI): {docs_url}\n")
      lines.append("FastAPI documentation: https://fastapi.tiangolo.com/\n\n")

      paths = spec.get("paths", {})
      for path, methods in sorted(paths.items()):
        for method, details in sorted(methods.items()):
          params = details.get("parameters", [])
          param_bits = []
          for p in params:
            name = p.get("name")
            where = p.get("in")
            required = p.get("required", False)
            schema = p.get("schema", {})
            ptype = schema.get("type", "")
            param_bits.append(
              f"{name} ({where}{', required' if required else ''}{', ' + ptype if ptype else ''})"
            )

          if param_bits:
            lines.append(f"{method.upper()} {path} - params: " + ", ".join(param_bits) + "\n")
          else:
            lines.append(f"{method.upper()} {path}\n")

      print("".join(lines), end="")
      PY

          # Create complete-DATE-TIME.zip containing source + docker config
          docker rm -f "$ZIP_NAME" >/dev/null 2>&1 || true
          docker create --name "$ZIP_NAME" -w /work python:3.12-slim \
            python - <<'PY'
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ts = datetime.now().strftime("%Y%m%d-%H%M%S")
out_dir = Path("artifacts")
out_dir.mkdir(exist_ok=True)

zip_name = out_dir / f"complete-{ts}.zip"

include_paths = [
    Path("api.py"),
    Path("convertToJSON.py"),
    Path("dashboard.py"),
    Path("seed_mongo.py"),
    Path("requirements.txt"),
    Path("Dockerfile"),
    Path("docker-compose.yaml"),
    Path("Jenkinsfile"),
    Path("README.txt"),
    Path("postman"),
    Path("data"),
]

def add_path(zipf: ZipFile, p: Path) -> None:
    if p.is_dir():
        for sub in sorted(p.rglob("*")):
            if sub.is_file():
                zipf.write(sub, sub.as_posix())
    elif p.is_file():
        zipf.write(p, p.as_posix())

with ZipFile(zip_name, "w", compression=ZIP_DEFLATED) as zipf:
    for p in include_paths:
        if p.exists():
            add_path(zipf, p)

print(zip_name.as_posix())
PY

          # Copy repo files into the zip container, create the zip there, then copy artifacts back.
          docker cp api.py "$ZIP_NAME:/work/api.py"
          docker cp convertToJSON.py "$ZIP_NAME:/work/convertToJSON.py"
          docker cp dashboard.py "$ZIP_NAME:/work/dashboard.py"
          docker cp seed_mongo.py "$ZIP_NAME:/work/seed_mongo.py"
          docker cp requirements.txt "$ZIP_NAME:/work/requirements.txt"
          docker cp Dockerfile "$ZIP_NAME:/work/Dockerfile"
          docker cp docker-compose.yaml "$ZIP_NAME:/work/docker-compose.yaml"
          docker cp Jenkinsfile "$ZIP_NAME:/work/Jenkinsfile"
          docker cp README.txt "$ZIP_NAME:/work/README.txt"
          docker cp postman "$ZIP_NAME:/work/postman"
          docker cp data "$ZIP_NAME:/work/data"

          docker start -a "$ZIP_NAME"
          rm -rf artifacts
          docker cp "$ZIP_NAME:/work/artifacts" artifacts
          docker rm -f "$ZIP_NAME" >/dev/null 2>&1 || true
        '''
      }
    }
  }

  post {
    always {
      sh '''
        set +e
        NETWORK="ci-${BUILD_NUMBER}"
        MONGO_NAME="mongo-ci-${BUILD_NUMBER}"
        API_NAME="api-ci-${BUILD_NUMBER}"

        docker rm -f "$API_NAME" >/dev/null 2>&1 || true
        docker rm -f "$MONGO_NAME" >/dev/null 2>&1 || true
        docker network rm "$NETWORK" >/dev/null 2>&1 || true
      '''

      // Make outputs easy to download from Jenkins
      archiveArtifacts artifacts: 'README.txt,newman-report.xml,artifacts/complete-*.zip', fingerprint: true, allowEmptyArchive: true
      junit testResults: 'newman-report.xml', allowEmptyResults: true

      echo 'Pipeline complete.'
    }
  }
}
