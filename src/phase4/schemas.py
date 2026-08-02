"""Phase 4 request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class Alert(BaseModel):
    severity: str
    metric: str
    value: float | str
    threshold: float | str | None = None
    target: str | None = None
    message: str


class MonitoringStatus(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    monitoring_interval_seconds: int
    continuous_learning_enabled: bool
    alerts: list[Alert]
    kpis: dict
    sla_compliance: dict


class DeploymentSpec(BaseModel):
    service_name: str
    env: str
    replicas: int
    autoscaling: dict
    sla: dict
    health_check: dict
    continuous_learning: bool


class RetrainResult(BaseModel):
    status: str
    triggered_by: str
    metadata: dict
    kpi_before: dict | None = None
    kpi_after: dict | None = None
    promoted: bool = False
