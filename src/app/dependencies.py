"""Shared application dependencies (singletons per process)."""

from src.phase1.pipeline import DiscoveryPipeline
from src.phase2.service import DiscoveryUIService
from src.phase3.ab_testing.experiment import ABTestManager
from src.phase3.analytics.dashboard import AnalyticsDashboard
from src.phase3.feedback.collector import FeedbackCollector
from src.phase3.service import ExperimentService
from src.phase4.learning.retrainer import ContinuousLearner
from src.phase4.monitoring.kpi_monitor import KPIMonitor
from src.phase4.service import ProductionService

discovery_pipeline = DiscoveryPipeline()
ui_service = DiscoveryUIService(discovery_pipeline)
feedback_collector = FeedbackCollector(discovery_pipeline.engine)
ab_manager = ABTestManager()
analytics = AnalyticsDashboard()

experiment_service = ExperimentService(ab_manager, analytics, feedback_collector)
kpi_monitor = KPIMonitor(analytics)
continuous_learner = ContinuousLearner(
    discovery_pipeline, feedback_collector, analytics
)
production_service = ProductionService(kpi_monitor, continuous_learner)
