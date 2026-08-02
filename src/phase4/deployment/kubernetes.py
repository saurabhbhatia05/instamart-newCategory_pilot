"""Generate Kubernetes deployment manifests — Phase 4."""

from config.settings import settings
from src.phase4.deployment.config import get_deployment_spec


def generate_kubernetes_manifest() -> dict:
    spec = get_deployment_spec()
    name = spec["service_name"]

    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "labels": {"app": name},
        },
        "spec": {
            "replicas": spec["replicas"],
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": {
                    "containers": [
                        {
                            "name": name,
                            "image": f"{name}:latest",
                            "ports": [{"containerPort": settings.app_port}],
                            "resources": spec["resources"],
                            "livenessProbe": {
                                "httpGet": {
                                    "path": spec["health_check"]["path"],
                                    "port": settings.app_port,
                                },
                                "periodSeconds": spec["health_check"][
                                    "interval_seconds"
                                ],
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": spec["health_check"]["path"],
                                    "port": settings.app_port,
                                },
                                "periodSeconds": 10,
                            },
                            "env": [
                                {"name": "APP_ENV", "value": spec["env"]},
                                {
                                    "name": "ENABLE_CONTINUOUS_LEARNING",
                                    "value": str(spec["continuous_learning"]).lower(),
                                },
                            ],
                        }
                    ]
                },
            },
        },
    }


def generate_hpa_manifest() -> dict:
    spec = get_deployment_spec()
    name = spec["service_name"]
    autoscale = spec["autoscaling"]

    return {
        "apiVersion": "autoscaling/v2",
        "kind": "HorizontalPodAutoscaler",
        "metadata": {"name": f"{name}-hpa"},
        "spec": {
            "scaleTargetRef": {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "name": name,
            },
            "minReplicas": autoscale["min_replicas"],
            "maxReplicas": autoscale["max_replicas"],
            "metrics": [
                {
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": autoscale[
                                "target_cpu_utilization"
                            ],
                        },
                    },
                }
            ],
        },
    }


def generate_service_manifest() -> dict:
    name = get_deployment_spec()["service_name"]
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": name},
        "spec": {
            "selector": {"app": name},
            "ports": [
                {
                    "port": 80,
                    "targetPort": settings.app_port,
                }
            ],
            "type": "LoadBalancer",
        },
    }
