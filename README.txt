(FastAPI + MongoDB Inventory API)

Jenkins one-click redeploy

1) Start Jenkins
	- docker compose --profile jenkins up -d --build
	- Open http://localhost:8081

2) Create a Pipeline job
	- New Item -> Pipeline
	- Pipeline -> Definition: "Pipeline script from SCM"
	- SCM: Git
	- Repository URL: (this repo)
	- Script Path: Jenkinsfile

3) Redeploy
	- Click "Build Now"
	- The pipeline will:
	  - Run tests via pytest
	  - Redeploy the app stack using: docker compose -f docker-compose.yaml up -d --build

App URLs
- API: http://localhost:8000/
- Jenkins: http://localhost:8081/
