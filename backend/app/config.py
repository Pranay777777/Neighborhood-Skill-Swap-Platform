from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET = "dev-only-change-me-dev-only-change-me"  # noqa: S105 - refused outside SQLite


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWAP_", env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./swap.db"
    jwt_secret: str = DEV_SECRET
    access_ttl_minutes: int = 15
    refresh_ttl_days: int = 7
    verify_ttl_hours: int = 24
    reset_ttl_minutes: int = 30
    app_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    mail_from: str = "Skill Swap <noreply@skillswap.local>"
    # "smtp" sends via SMTP (Mailpit in dev); "console" only logs the mail.
    mail_backend: str = "smtp"
    # Restore the demo accounts and their posts on every start (live demo, E2E).
    seed_demo: bool = False
    # Rate limits per client on password and mail endpoints ("N/period", see slowapi).
    rate_limit_enabled: bool = True
    rate_limit_login: str = "10/minute"
    rate_limit_register: str = "10/hour"
    rate_limit_forgot: str = "5/hour"
    # Set only behind a proxy that appends the client to X-Forwarded-For (Render).
    trust_proxy: bool = False

    @field_validator("database_url")
    @classmethod
    def use_psycopg3(cls, url: str) -> str:
        """Hosted Postgres (Neon) hands out postgres:// or postgresql:// URLs; use psycopg 3."""
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url


settings = Settings()
