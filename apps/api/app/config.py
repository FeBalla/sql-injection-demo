"""Application settings, read from environment variables (see docker-compose.yml)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    database_url: str = ""
    """Postgres connection string for the least-privilege app role. Empty disables Postgres."""

    gcp_project_id: str = ""
    """Project that runs BigQuery jobs. Empty disables BigQuery."""

    bq_dataset: str = "injection_lab"
    bq_table: str = "customers"
    bq_location: str = "US"

    bq_job_timeout_ms: int = 30_000
    """Upper bound for any BigQuery job; the client also cancels jobs it stops waiting for."""

    statement_timeout_ms: int = 5000
    """Upper bound for any Postgres statement, so injected SQL cannot hog the database."""
