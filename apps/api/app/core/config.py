from functools import lru_cache

from cryptography.fernet import Fernet
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DeckPilot"
    environment: str = Field(default="development", alias="APP_ENV")
    api_base_url: str = Field(default="http://localhost:8000", alias="API_BASE_URL")
    web_base_url: str = Field(default="http://localhost:3000", alias="WEB_BASE_URL")
    database_url: str = Field(default="postgresql+psycopg://deckpilot:deckpilot@postgres:5432/deckpilot", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    secret_key: str = Field(alias="SECRET_KEY")
    encryption_key: str = Field(alias="ENCRYPTION_KEY")
    session_cookie_name: str = Field(default="deckpilot_session", alias="SESSION_COOKIE_NAME")
    csrf_cookie_name: str = Field(default="deckpilot_csrf", alias="CSRF_COOKIE_NAME")
    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_samesite: str = Field(default="lax", alias="COOKIE_SAMESITE")
    session_ttl_minutes: int = 60 * 24 * 7
    steam_api_key: str = Field(default="", alias="STEAM_API_KEY")
    steam_test_mode: bool = Field(default=True, alias="STEAM_TEST_MODE")
    steam_integration_mode: str = Field(default="demo", alias="STEAM_INTEGRATION_MODE")
    steam_official_linking_enabled: bool = Field(default=False, alias="STEAM_OFFICIAL_LINKING_ENABLED")
    allow_demo_mode_in_production: bool = Field(default=False, alias="ALLOW_DEMO_MODE_IN_PRODUCTION")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin-change-me", alias="ADMIN_PASSWORD")
    seed_demo_user: bool = Field(default=False, alias="SEED_DEMO_USER")
    demo_username: str = Field(default="demo", alias="DEMO_USERNAME")
    demo_password: str = Field(default="demo-password-123", alias="DEMO_PASSWORD")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    billing_provider: str = Field(default="mock", alias="BILLING_PROVIDER")
    billing_currency: str = Field(default="USD", alias="BILLING_CURRENCY")
    coinbase_api_key: str = Field(default="", alias="COINBASE_API_KEY")
    coinbase_webhook_secret: str = Field(default="", alias="COINBASE_WEBHOOK_SECRET")
    coinbase_charge_url: str = Field(default="https://api.commerce.coinbase.com/charges", alias="COINBASE_CHARGE_URL")
    enable_lifetime_checkout: bool = Field(default=False, alias="ENABLE_LIFETIME_CHECKOUT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    sentry_traces_sample_rate: float = Field(default=0.0, alias="SENTRY_TRACES_SAMPLE_RATE")
    email_provider: str = Field(default="console", alias="EMAIL_PROVIDER")
    email_from: str = Field(default="DeckPilot <no-reply@deckpilot.local>", alias="EMAIL_FROM")
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        allowed = {"development", "test", "production"}
        if value not in allowed:
            raise ValueError(f"APP_ENV must be one of {sorted(allowed)}")
        return value

    @field_validator("billing_provider")
    @classmethod
    def validate_billing_provider(cls, value: str) -> str:
        allowed = {"mock", "coinbase"}
        if value not in allowed:
            raise ValueError(f"BILLING_PROVIDER must be one of {sorted(allowed)}")
        return value

    @field_validator("email_provider")
    @classmethod
    def validate_email_provider(cls, value: str) -> str:
        allowed = {"console", "smtp"}
        normalized = value.lower()
        if normalized not in allowed:
            raise ValueError(f"EMAIL_PROVIDER must be one of {sorted(allowed)}")
        return normalized

    @field_validator("steam_integration_mode")
    @classmethod
    def validate_steam_integration_mode(cls, value: str) -> str:
        normalized = value.lower()
        allowed = {"demo", "official"}
        if normalized not in allowed:
            raise ValueError(f"STEAM_INTEGRATION_MODE must be one of {sorted(allowed)}")
        return normalized

    @field_validator("cookie_domain", mode="before")
    @classmethod
    def normalize_cookie_domain(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value

    @field_validator("cookie_samesite")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        normalized = value.lower()
        allowed = {"lax", "strict", "none"}
        if normalized not in allowed:
            raise ValueError(f"COOKIE_SAMESITE must be one of {sorted(allowed)}")
        return normalized

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return value

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, value: str) -> str:
        Fernet(value.encode("utf-8"))
        return value

    @model_validator(mode="after")
    def validate_production_settings(self):
        weak_secret_markers = ("change-me", "replace-", "admin-change-me", "secret-key", "your-secret")
        known_sample_fernet_keys = {"0J4FyJwHnYmeFz7r5Zk8F0KJxl-2mFY9hqqIetQxZj0="}
        local_public_hosts = ("localhost", "127.0.0.1", "0.0.0.0", "::1")

        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise ValueError("COOKIE_SECURE=true is required when COOKIE_SAMESITE=none")

        if self.environment == "production":
            if self.secret_key.startswith(weak_secret_markers):
                raise ValueError("SECRET_KEY must be replaced before production")
            if self.encryption_key in known_sample_fernet_keys:
                raise ValueError("ENCRYPTION_KEY must be generated uniquely before production")
            if self.admin_password.startswith(weak_secret_markers) or len(self.admin_password) < 12:
                raise ValueError("ADMIN_PASSWORD must be replaced before production")
            if not self.api_base_url.startswith("https://"):
                raise ValueError("API_BASE_URL must use HTTPS in production")
            if not self.web_base_url.startswith("https://"):
                raise ValueError("WEB_BASE_URL must use HTTPS in production")
            if any(host in self.api_base_url.lower() for host in local_public_hosts):
                raise ValueError("API_BASE_URL must not point to a local host in production")
            if any(host in self.web_base_url.lower() for host in local_public_hosts):
                raise ValueError("WEB_BASE_URL must not point to a local host in production")
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE=true is required in production")
            if self.billing_provider == "mock":
                raise ValueError("BILLING_PROVIDER=mock is forbidden in production")
            if self.billing_provider == "coinbase" and (not self.coinbase_api_key or not self.coinbase_webhook_secret):
                raise ValueError("Coinbase credentials are required in production")
            if self.database_url.startswith("sqlite"):
                raise ValueError("DATABASE_URL must not use SQLite in production")
            if not self.redis_url:
                raise ValueError("REDIS_URL is required in production")
            if self.email_provider == "smtp" and not self.smtp_host:
                raise ValueError("SMTP_HOST is required when EMAIL_PROVIDER=smtp")
            origins = self.cors_origin_list
            if not origins or "*" in origins:
                raise ValueError("Wildcard or empty CORS_ORIGINS is forbidden in production")
            if self.web_base_url.rstrip("/") not in {origin.rstrip("/") for origin in origins}:
                raise ValueError("CORS_ORIGINS must include WEB_BASE_URL in production")
            demo_runtime = self.steam_test_mode or self.steam_integration_mode == "demo"
            if demo_runtime and not self.allow_demo_mode_in_production:
                raise ValueError("ALLOW_DEMO_MODE_IN_PRODUCTION=true is required when STEAM_TEST_MODE=true in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
