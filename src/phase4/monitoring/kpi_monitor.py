"""KPI monitoring and production health — Phase 4."""

from datetime import datetime

from config.settings import settings
from src.phase3.analytics.dashboard import AnalyticsDashboard
from src.phase4.schemas import Alert, MonitoringStatus


class KPIMonitor:
    """Phase 4: Continuous KPI monitoring, alerting, and SLA checks."""

    CONVERSION_WARNING_THRESHOLD = 5.0
    NORTH_STAR_TARGET = 15.0
    LATENCY_SLA_MS = settings.recommendation_latency_ms

    def __init__(self, dashboard: AnalyticsDashboard | None = None) -> None:
        self.dashboard = dashboard or AnalyticsDashboard()
        self._alerts: list[Alert] = []
        self._check_count = 0

    def check_thresholds(self) -> list[Alert]:
        summary = self.dashboard.get_kpi_summary()
        kpis = summary["kpis"]
        alerts: list[Alert] = []

        if kpis["recommendation_conversion"] < self.CONVERSION_WARNING_THRESHOLD:
            alerts.append(
                Alert(
                    severity="warning",
                    metric="recommendation_conversion",
                    value=kpis["recommendation_conversion"],
                    threshold=self.CONVERSION_WARNING_THRESHOLD,
                    message="Conversion below target — review model confidence threshold",
                )
            )

        if kpis["cross_category_purchase_rate"] < self.NORTH_STAR_TARGET:
            alerts.append(
                Alert(
                    severity="info",
                    metric="cross_category_purchase_rate",
                    value=kpis["cross_category_purchase_rate"],
                    target=f"+{self.NORTH_STAR_TARGET}%",
                    message="Tracking toward +15% cross-category KPI target",
                )
            )

        if kpis["recommendation_ctr"] < 3.0 and summary["counts"]["impressions"] > 10:
            alerts.append(
                Alert(
                    severity="warning",
                    metric="recommendation_ctr",
                    value=kpis["recommendation_ctr"],
                    threshold=3.0,
                    message="Low recommendation CTR — review card relevance",
                )
            )

        self._alerts.extend(alerts)
        self._check_count += 1
        return alerts

    def check_sla_compliance(self, last_latency_ms: float | None = None) -> dict:
        return {
            "availability_target": "99.9%",
            "latency_sla_ms": self.LATENCY_SLA_MS,
            "last_latency_ms": last_latency_ms,
            "latency_ok": last_latency_ms is None
            or last_latency_ms <= self.LATENCY_SLA_MS,
            "max_recommendations_per_session": settings.max_recommendations_per_session,
        }

    def get_status(self, last_latency_ms: float | None = None) -> MonitoringStatus:
        new_alerts = self.check_thresholds()
        return MonitoringStatus(
            monitoring_interval_seconds=settings.kpi_monitoring_interval_seconds,
            continuous_learning_enabled=settings.enable_continuous_learning,
            alerts=new_alerts or self._alerts[-5:],
            kpis=self.dashboard.get_kpi_summary(),
            sla_compliance=self.check_sla_compliance(last_latency_ms),
        )

    def get_alert_history(self, limit: int = 20) -> list[dict]:
        return [a.model_dump() for a in self._alerts[-limit:]]
