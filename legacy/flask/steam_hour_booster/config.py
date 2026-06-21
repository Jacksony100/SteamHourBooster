import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///steam_accounts.db")
    STEAM_API_KEY = os.getenv("STEAM_API_KEY", "")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY", "")
    COINBASE_WEBHOOK_SECRET = os.getenv("COINBASE_WEBHOOK_SECRET", "")
    COINBASE_CHARGE_URL = os.getenv(
        "COINBASE_CHARGE_URL",
        "https://api.commerce.coinbase.com/charges",
    )
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")
    TESTING = False
    JSON_SORT_KEYS = False
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1") == "1"
    CSRF_ENABLED = os.getenv("CSRF_ENABLED", "1") == "1"
    CSRF_EXEMPT_PATHS = {"/coinbase/webhook"}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv(
        "SESSION_COOKIE_SECURE",
        "1" if FLASK_ENV == "production" else "0",
    ) == "1"
    PERMANENT_SESSION_LIFETIME = int(os.getenv("SESSION_LIFETIME_SECONDS", "604800"))

    @classmethod
    def load_encryption_key(cls) -> str:
        if cls.ENCRYPTION_KEY:
            return cls.ENCRYPTION_KEY
        raise RuntimeError("ENCRYPTION_KEY must be set in the environment.")


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key-that-is-long-enough"
    RATE_LIMIT_ENABLED = False
    CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
