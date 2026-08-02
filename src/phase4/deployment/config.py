"""Production deployment configuration — Phase 4."""

from config.settings import settings

PRODUCTION_CONFIG = {
    "service_name": "smart-discovery-assistant",
    "replicas": 3,
    "resources": {
        "cpu": "500m",
        "memory": "512Mi",
    },
    "autoscaling": {
        "min_replicas": 2,
        "max_replicas": 20,
        "target_cpu_utilization": 70,
    },
    "sla": {
        "availability": "99.9%",
        "recommendation_latency_ms": settings.recommendation_latency_ms,
        "max_recommendations_per_session": settings.max_recommendations_per_session,
    },
    "health_check": {
        "path": "/health",
        "interval_seconds": 30,
    },
}


def get_deployment_spec() -> dict:
    return {
        **PRODUCTION_CONFIG,
        "env": settings.app_env,
        "continuous_learning": settings.enable_continuous_learning,
    }
