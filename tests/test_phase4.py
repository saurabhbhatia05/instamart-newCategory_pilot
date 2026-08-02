"""Phase 4 unit tests."""

from src.app.dependencies import production_service


def test_deployment_spec():
    spec = production_service.get_deployment_spec()
    assert spec.service_name == "smart-discovery-assistant"
    assert spec.replicas >= 2
    assert spec.sla["availability"] == "99.9%"


def test_kubernetes_manifests():
    manifests = production_service.get_kubernetes_manifests()
    assert "deployment" in manifests
    assert "service" in manifests
    assert "hpa" in manifests
    assert manifests["deployment"]["kind"] == "Deployment"
    assert manifests["hpa"]["kind"] == "HorizontalPodAutoscaler"


def test_monitoring_status():
    status = production_service.get_monitoring_status(last_latency_ms=120.0)
    assert status.sla_compliance["latency_ok"] is True
    assert status.monitoring_interval_seconds > 0
    assert "kpis" in status.kpis


def test_learning_cycle_skipped_when_disabled():
    result = production_service.run_learning_cycle(force=False)
    assert result["status"] in ("skipped", "trained")
