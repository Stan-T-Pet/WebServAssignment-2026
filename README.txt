# WebServ Assignment 2026

This repository contains a containerised inventory service built with FastAPI and MongoDB, plus a lightweight monitoring dashboard, Prometheus, Grafana, and a Jenkins pipeline for automated validation and redeployment.

The README is aligned to the current implementation in the repository. The existing README.txt is kept as a pipeline-generated artifact and should not be treated as the main project overview.

## Project Scope

The current implementation covers these assignment-style deliverables:

- REST API for product inventory operations
- MongoDB-backed persistence
- CSV to JSON data preparation
- Seed script for loading product data into MongoDB
- Docker image and Docker Compose orchestration
- Automated tests with pytest
- API checks through Postman/Newman in Jenkins
- Prometheus metrics exposure and scraping
- Grafana datasource and dashboard provisioning
- Simple monitoring dashboard service

## Current Architecture

- api.py: FastAPI inventory API with MongoDB integration and Prometheus instrumentation
- dashboard.py: small FastAPI service exposing monitoring links and a health summary
- convertToJSON.py: converts data/products.csv into data/products.json
- seed_mongo.py: seeds MongoDB from data/products.json
- docker-compose.yaml: runs MongoDB, API, Prometheus, Grafana, dashboard, and Jenkins
- Jenkinsfile: pulls from GitHub, runs tests, starts isolated CI containers, runs Newman tests, and archives outputs

## Implemented API Endpoints

Base URL: http://localhost:8000

- GET / - API status and endpoint listing
- GET /getSingleProduct/{product_id} - fetch one product by ProductID
- GET /getAll - return all products
- POST /addNew - create a product using query parameters
- DELETE /deleteOne/{product_id} - delete a product by ProductID
- GET /startsWith/{letter} - filter products by first letter of Name
- GET /paginate/{start_id}/{end_id} - return up to 10 products in a ProductID range
- GET /convert/{product_id} - convert a product price from USD to EUR using a live exchange-rate API
- GET /docs - FastAPI Swagger UI
- GET /openapi.json - OpenAPI specification
- GET /metrics - Prometheus metrics exposed by the API

## Monitoring And Observability

The API is instrumented with prometheus-fastapi-instrumentator, and Prometheus scrapes the application metrics endpoint. Grafana is preconfigured with a Prometheus datasource through the provisioning files in grafana/provisioning.

Services:

- API: http://localhost:8000
- API Swagger docs: http://localhost:8000/docs
- API metrics: http://localhost:8000/metrics
- Dashboard: http://localhost:8001
- Dashboard health endpoint: http://localhost:8001/health
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Jenkins: http://localhost:8081

Grafana defaults:

- Username: admin
- Password: admin

The dashboard service currently provides quick links plus a basic health check for the API and Prometheus. It is not a full UI dashboard.

## Running The Project

### Option 1: Docker Compose

From the project root:

powershell
docker compose up -d --build


Then seed the database from inside the API container:

powershell
docker compose exec api python3 seed_mongo.py


If you want live currency conversion through the official ExchangeRate API, set EXCHANGE_RATE_API_KEY before starting the stack. If it is not set, the API falls back to https://open.er-api.com/v6/latest/USD.

### Option 2: Local Python Environment

Install dependencies:

powershell
pip install -r requirements.txt


Start MongoDB separately, then run:

powershell
uvicorn api:app --reload


To seed locally, ensure MONGO_URI and optionally MONGO_DB are set, then run:

powershell
python seed_mongo.py


## Data Preparation

The product dataset is stored in data/products.csv and data/products.json.

To regenerate the JSON file from CSV:

powershell
python convertToJSON.py


To seed MongoDB:

powershell
python seed_mongo.py


Required environment variable for seeding outside Docker:

- MONGO_URI, for example mongodb://admin:adminPassword123@localhost:27017/?authSource=admin

Optional environment variables:

- MONGO_DB default: inventory_db
- EXCHANGE_RATE_API_KEY default: empty string

## Testing

Unit tests are in tests/test_api.py and use fastapi.testclient with mocked MongoDB and HTTP calls.

Run tests locally with:

powershell
pytest -q


The Jenkins pipeline also runs Postman/Newman tests from postman/InventoryAPI.postman_collection.json against the running API container.

## Jenkins Pipeline

The pipeline in Jenkinsfile currently performs these steps:

1. Pulls the repository from GitHub.
2. Builds the API Docker image.
3. Starts an isolated MongoDB container for the CI run.
4. Runs pytest inside the built image.
5. Seeds MongoDB with the product dataset.
6. Starts the API container in the CI network.
7. Executes the Postman collection with Newman.
8. Generates a README.txt endpoint summary and a zip artifact.
9. Archives the generated reports and artifacts in Jenkins.

To start Jenkins with the rest of the stack:

powershell
docker compose up -d --build


Then create a Pipeline job in Jenkins pointing to this repository and using Jenkinsfile as the script path.

## Notes On Current Implementation

- Product values such as UnitPrice and StockQuantity are stored as strings in MongoDB by the current API implementation.
- POST /addNew accepts data through query parameters rather than a JSON request body.
- GET /paginate/{start_id}/{end_id} sorts by ProductID and returns at most 10 records.
- The monitoring dashboard is API-based rather than a custom frontend page.
- README.txt is generated by the Jenkins pipeline and may be overwritten during CI runs.

## Repository Structure

text
api.py
convertToJSON.py
dashboard.py
docker-compose.yaml
Dockerfile
Jenkinsfile
prometheus.yml
README.txt
requirements.txt
seed_mongo.py
data/
grafana/
jenkins/
postman/
tests/
