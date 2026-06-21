import pytest
from app.core.config import Settings
from pydantic import ValidationError

VALID_PRODUCTION_ENV = {
    "APP_ENV": "production",
    "API_BASE_URL": "https://deckpilot.example.com",
    "WEB_BASE_URL": "https://deckpilot.example.com",
    "DATABASE_URL": "postgresql+psycopg://deckpilot:deckpilot@postgres:5432/deckpilot",
    "REDIS_URL": "redis://redis:6379/0",
    "SECRET_KEY": "production-secret-key-that-is-long-enough-and-random",
    "ENCRYPTION_KEY": "kPmjn7yo5VwDl4ASYHDvksmz-jluxo5_ivnutlxBA9E=",
    "ADMIN_PASSWORD": "admin-password-that-is-strong-enough",
    "CORS_ORIGINS": "https://deckpilot.example.com",
    "COOKIE_SECURE": True,
    "COOKIE_SAMESITE": "lax",
    "BILLING_PROVIDER": "coinbase",
    "COINBASE_API_KEY": "coinbase-api-key",
    "COINBASE_WEBHOOK_SECRET": "coinbase-webhook-secret",
    "STEAM_TEST_MODE": False,
    "STEAM_INTEGRATION_MODE": "official",
}


def make_settings(**overrides):
    return Settings(**{**VALID_PRODUCTION_ENV, **overrides})


def test_valid_production_settings_pass():
    settings = make_settings()

    assert settings.environment == "production"
    assert settings.cookie_secure is True
    assert settings.billing_provider == "coinbase"
    assert settings.session_cookie_name == "deckpilot_session"
    assert settings.csrf_cookie_name == "deckpilot_csrf"


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"BILLING_PROVIDER": "mock"}, "BILLING_PROVIDER=mock is forbidden"),
        ({"COOKIE_SECURE": False}, "COOKIE_SECURE=true is required"),
        ({"DATABASE_URL": "sqlite:///./prod.db"}, "DATABASE_URL must not use SQLite"),
        ({"CORS_ORIGINS": "*"}, "Wildcard or empty CORS_ORIGINS"),
        ({"API_BASE_URL": "http://deckpilot.example.com"}, "API_BASE_URL must use HTTPS"),
        ({"WEB_BASE_URL": "http://deckpilot.example.com"}, "WEB_BASE_URL must use HTTPS"),
        ({"API_BASE_URL": "https://localhost"}, "API_BASE_URL must not point to a local host"),
        ({"WEB_BASE_URL": "https://127.0.0.1"}, "WEB_BASE_URL must not point to a local host"),
        ({"ENCRYPTION_KEY": "0J4FyJwHnYmeFz7r5Zk8F0KJxl-2mFY9hqqIetQxZj0="}, "ENCRYPTION_KEY must be generated uniquely"),
        ({"STEAM_TEST_MODE": True, "ALLOW_DEMO_MODE_IN_PRODUCTION": False}, "ALLOW_DEMO_MODE_IN_PRODUCTION=true is required"),
        ({"STEAM_INTEGRATION_MODE": "demo", "ALLOW_DEMO_MODE_IN_PRODUCTION": False}, "ALLOW_DEMO_MODE_IN_PRODUCTION=true is required"),
    ],
)
def test_invalid_production_settings_fail_fast(override, message):
    with pytest.raises(ValidationError, match=message):
        make_settings(**override)


def test_demo_mode_in_production_requires_explicit_flag():
    settings = make_settings(STEAM_TEST_MODE=True, ALLOW_DEMO_MODE_IN_PRODUCTION=True)

    assert settings.steam_test_mode is True
    assert settings.allow_demo_mode_in_production is True


def test_samesite_none_requires_secure_cookie_outside_production():
    with pytest.raises(ValidationError, match="COOKIE_SECURE=true is required when COOKIE_SAMESITE=none"):
        Settings(
            APP_ENV="development",
            SECRET_KEY="development-secret-key-that-is-long-enough",
            ENCRYPTION_KEY="kPmjn7yo5VwDl4ASYHDvksmz-jluxo5_ivnutlxBA9E=",
            COOKIE_SAMESITE="none",
            COOKIE_SECURE=False,
        )


def test_empty_cookie_domain_is_normalized_to_none():
    settings = Settings(
        APP_ENV="development",
        SECRET_KEY="development-secret-key-that-is-long-enough",
        ENCRYPTION_KEY="kPmjn7yo5VwDl4ASYHDvksmz-jluxo5_ivnutlxBA9E=",
        COOKIE_DOMAIN="",
    )

    assert settings.cookie_domain is None
