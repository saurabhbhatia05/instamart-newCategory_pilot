"""Central configuration loaded from environment variables."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Survey
    survey_pdf_path: Path = PROJECT_ROOT / "data" / "survey" / "responses.pdf"

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # Phase 1
    recommendation_confidence_threshold: float = 0.65
    max_recommendations_per_session: int = 1
    recommendation_latency_ms: int = 500

    # Phase 2 — Grok LLM (optional explainability enhancement)
    grok_api_key: str | None = Field(default=None, validation_alias="GROK_API_KEY")
    groq_api_key: str | None = Field(default=None, validation_alias="GROQ_API_KEY")
    grok_model: str = "grok-2-latest"
    groq_model: str = "llama-3.3-70b-versatile"
    grok_api_base: str = "https://api.x.ai/v1"
    groq_api_base: str = "https://api.groq.com/openai/v1"
    use_llm: bool = False

    # Phase 3
    ab_test_enabled: bool = True
    ab_test_control_ratio: float = 0.5

    # Phase 4
    enable_continuous_learning: bool = False
    kpi_monitoring_interval_seconds: int = 300

    @property
    def survey_pdf_resolved(self) -> Path:
        path = self.survey_pdf_path
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    @property
    def llm_enabled(self) -> bool:
        return self.use_llm and self.llm_api_key is not None

    @property
    def llm_api_key(self) -> str | None:
        return self.grok_api_key or self.groq_api_key

    @property
    def llm_model(self) -> str:
        if self.grok_api_key:
            return self.grok_model
        return self.groq_model

    @property
    def llm_api_base(self) -> str:
        if self.grok_api_key:
            return self.grok_api_base.rstrip("/")
        return self.groq_api_base.rstrip("/")

    @property
    def llm_provider(self) -> str:
        return "grok" if self.grok_api_key else "groq"


settings = Settings()
