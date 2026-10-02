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


settings = Settings()
