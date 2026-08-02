"""Phase 4 orchestration — deployment, monitoring, continuous learning."""

from src.phase4.deployment.config import get_deployment_spec
from src.phase4.deployment.kubernetes import (
    generate_hpa_manifest,
    generate_kubernetes_manifest,
    generate_service_manifest,
)
from src.phase4.learning.retrainer import ContinuousLearner
from src.phase4.monitoring.kpi_monitor import KPIMonitor
from src.phase4.schemas import DeploymentSpec, MonitoringStatus


class ProductionService:
    """Phase 4 entry point for rollout, monitoring, and learning."""

    def __init__(
        self,
        kpi_monitor: KPIMonitor,
        continuous_learner: ContinuousLearner,
    ) -> None:
        self.monitor = kpi_monitor
        self.learner = continuous_learner

    def get_deployment_spec(self) -> DeploymentSpec:
        spec = get_deployment_spec()
        return DeploymentSpec(
            service_name=spec["service_name"],
            env=spec["env"],
            replicas=spec["replicas"],
            autoscaling=spec["autoscaling"],
            sla=spec["sla"],
            health_check=spec["health_check"],
            continuous_learning=spec["continuous_learning"],
        )

    def get_kubernetes_manifests(self) -> dict:
        return {
            "deployment": generate_kubernetes_manifest(),
            "service": generate_service_manifest(),
            "hpa": generate_hpa_manifest(),
        }

    def get_monitoring_status(
        self, last_latency_ms: float | None = None
    ) -> MonitoringStatus:
        return self.monitor.get_status(last_latency_ms)

    def run_learning_cycle(self, force: bool = False) -> dict:
        result = self.learner.retrain(force=force)
        if result.get("status") == "trained":
            self.monitor.check_thresholds()
        return result

    def get_learning_status(self) -> dict:
        return self.learner.get_status()
