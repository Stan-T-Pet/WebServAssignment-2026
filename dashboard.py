# API Dashboard 
from fastapi import FastAPI, HTTPException
import requests
app = FastAPI()

# Monitoring stack URLs for easy access from the dashboard
PROMETHEUS_URL = "http://localhost:9090"
GRAFANA_URL = "http://localhost:3000"
API_METRICS_URL = "http://localhost:8000/metrics"


@app.get("/")
def dashboard_info():
    return {
        "message": "Inventory API Monitoring Dashboard",
        "prometheus": PROMETHEUS_URL,
        "grafana": GRAFANA_URL,
        "api_metrics": API_METRICS_URL,
        "instructions": {
            "grafana_login": "http://localhost:3000",
            "add_dashboard": "In Grafana, go to Dashboards > Import > enter ID 14282 for a FastAPI Prometheus dashboard"
        }
    }


@app.get("/health")
def health():
    results = {}
    for name, url in [("api", "http://localhost:8000/"), ("prometheus", f"{PROMETHEUS_URL}/-/healthy")]:
        try:
            r = requests.get(url, timeout=5)
            results[name] = "up" if r.status_code < 400 else "degraded"
        except requests.RequestException:
            results[name] = "down"
    return results

