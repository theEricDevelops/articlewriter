import os

# Define root paths
API_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(API_ROOT)

CONFIG_DEFAULTS: dict = {
    "GLOBAL": {
        "ENVIRONMENT": "development",
        "PORT": 8000,
        "DEBUG": False,
        "LOG_LEVEL": "info",
        "SECRET_KEY": "default_insecure_key_01234567890_"
    },
    "DATABASE": {
        "DB_NAME": "app",
        "DB_DIR": "sqlite_data",
        "DB_TYPE": "sqlite"
    },
    "DB_TYPES": {
        "POSTGRESQL": {
            "DB_NAME": "app",
            "DB_USER": "postgres",
            "DB_PASSWORD": "Postgres123!",
            "DB_HOST": "localhost",
            "DB_PORT": 5432,
            "ALIASES": ["postgresql", "postgres"]
        },
        "SQLITE": {
            "DB_NAME": "app",
            "DB_DIR": "sqlite_data",
            "ALIASES": ["sqlite"]
        }
    },
    "USER": {
        "DEFAULT_ROLE": "viewer"
    },
    "AI": {
        "DEFAULT_PROVIDER": "xai",
        "DEFAULT_MODEL": "grok-2-1212",
        "API_KEY": "your_api_key"
    }
}