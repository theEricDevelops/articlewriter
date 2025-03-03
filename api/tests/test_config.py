import copy
import pytest
from app.config import Config
from pydantic import ValidationError
from pathlib import Path
import configparser
from app.constants import *
from app.config import *

# Helper function to create temporary INI files
def create_ini_file(tmp_path: Path, config_data: dict = None, tmp_file: str = "config.ini") -> Path:
    ini_file = tmp_path / tmp_file
    parser = configparser.ConfigParser()

    for section, values in config_data.items():
        parser[section] = values
    
    # Debug output
    print(f"Writing config with sections: {list(config_data.keys())} to {ini_file}")
    for section, values in config_data.items():
        print(f"  {section}: {values}")

    with ini_file.open("w") as f:
        parser.write(f)
    
    return ini_file

# Valid configuration data for SQLite
VALID_SQLITE_CONFIG = {
    "GLOBAL": {
        "ENV_MODE": "development",
        "PORT": 5000,
        "LOG_LEVEL": "info",
        "DEBUG": True,
        "SECRET_KEY": "CZ4WaeAaJYlU7lPtDBXQ11BFKOAl1ifWh9sgUx_URdVG6O4wz0yWQP2xgoxLA8B30zIkkhqsGant5QVNPWd6kA"
    },
    "DATABASE": {
        "DB_TYPE": "sqlite",
        "DB_NAME": "sqlite_db"
    },
    "SQLITE": {
        "DB_DIR": "sqlite_data"
    },
    "USER": {
        "DEFAULT_ROLE": "viewer"
    },
    "AI": {
        "DEFAULT_PROVIDER": "xai",
        "DEFAULT_MODEL": "grok-2-1212",
        "API_KEY": "secret_key123"
    }
}

# Valid configuration data for PostgreSQL
VALID_POSTGRESQL_CONFIG = {
    "GLOBAL": {
        "ENV_MODE": "production",
        "PORT": 5432,
        "LOG_LEVEL": "error",
        "DEBUG": False,
        "SECRET_KEY": "0p1oEpK6KfVxia7cMYl3HQz4eN7wfvG32c6gNkHJfbxRQ0AX-um_yZwHcqTGQTxkDI7Sd4R7O42oN63JR4E3mw"
    },
    "DATABASE": {
        "DB_TYPE": "postgresql",
        "DB_NAME": "postgres_db"
    },
    "POSTGRESQL": {
        "DB_USER": "postgres_test_user",
        "DB_PASSWORD": "Postgres_Test_P@ss123",
        "DB_HOST": "testhost",
        "DB_PORT": "8888"
    },
    "USER": {
        "DEFAULT_ROLE": "admin"
    },
    "AI": {
        "DEFAULT_PROVIDER": "openai",
        "DEFAULT_MODEL": "gpt-3.5",
        "API_KEY": "openai_api_key"
    }
}

def test_valid_sqlite_config(tmp_path):
    ini_file = create_ini_file(tmp_path, VALID_SQLITE_CONFIG)
    config = Config.load_config(str(ini_file))
    assert config.global_.env == "development"
    assert config.global_.port == 5000
    assert config.global_.log_level == "info"
    assert config.global_.debug is True
    assert config.global_.secret == VALID_SQLITE_CONFIG["GLOBAL"]["SECRET_KEY"]
    assert config.db.type == "sqlite"
    assert config.db.name == "sqlite_db"
    assert config.db.dir == "sqlite_data"
    assert config.user.default_role == "viewer"
    assert config.ai.default_provider == "xai"
    assert config.ai.default_model == "grok-2-1212"
    assert config.ai.api_key == VALID_SQLITE_CONFIG["AI"]["API_KEY"]

def test_valid_postgresql_config(tmp_path):
    ini_file = create_ini_file(tmp_path, VALID_POSTGRESQL_CONFIG)
    config = Config.load_config(str(ini_file))
    assert config.global_.env == "production", "Environment should be production"
    assert config.global_.port == 5432, "Global Port should be 5432"
    assert config.global_.log_level == "error", "Log level should be error"
    assert config.global_.debug is False, "Debug should be False"
    assert config.global_.secret == VALID_POSTGRESQL_CONFIG["GLOBAL"]["SECRET_KEY"]
    assert config.db.type == 'postgresql', "DB Type should be postgresql"
    assert config.db.name == "postgres_db", "DB Name should be postgres_db"
    assert config.db.user == "postgres_test_user", "DB User should be postgres_test_user"
    assert config.db.password == "Postgres_Test_P@ss123", "DB Password should be postgres_test_pass"
    assert config.db.host == "testhost", "DB Host should be postgres_test_host"
    assert config.db.port == 8888, "DB Port should be 8888"
    assert config.user.default_role == "admin"
    assert config.ai.default_provider == "openai"
    assert config.ai.default_model == "gpt-3.5"
    assert config.ai.api_key == VALID_POSTGRESQL_CONFIG["AI"]["API_KEY"]

@pytest.mark.parametrize("missing_section", ["GLOBAL", "DATABASE", "USER", "AI"])
def test_missing_sections(tmp_path, missing_section):
    config_data = copy.deepcopy(VALID_SQLITE_CONFIG)
    del config_data[missing_section]
    ini_file = create_ini_file(tmp_path, config_data)
    config = Config.load_config(str(ini_file))

    db_defaults = CONFIG_DEFAULTS["DATABASE"]
    db_defaults.update(CONFIG_DEFAULTS["DB_TYPES"]["SQLITE"])
    
    # Check that the missing section is set to the default value
    if missing_section == "GLOBAL":
        assert config.global_ == GlobalConfig(), "GlobalConfig should be default and got {config.global_}"
    elif missing_section == "DATABASE":
        assert config.db.type == db_defaults['DB_TYPE'], f"DB_TYPE should be {db_defaults['DB_TYPE']} and got {config.db.type}"
        assert config.db.name == db_defaults['DB_NAME'], f"DB_NAME should be {db_defaults['DB_NAME']} and got {config.db.name}"
        assert config.db.dir == db_defaults['DB_DIR'], f"DB_DIR should be {db_defaults['DB_DIR']} and got {config.db.dir}"
    elif missing_section == "USER":
        assert config.user == UserConfig(), "UserConfig should be default and got {config.user}"
    elif missing_section == "AI":
        assert config.ai == AIConfig(), "AIConfig should be default and got {config.ai}"

def test_invalid_database_type(tmp_path):
    config_data = copy.deepcopy(VALID_SQLITE_CONFIG)
    config_data["DATABASE"]["DB_TYPE"] = "mysql"
    ini_file = create_ini_file(tmp_path, config_data)
    with pytest.raises(ValueError, match="Unsupported DB_TYPE"):
        Config.load_config(str(ini_file))

def test_missing_sqlite_section(tmp_path):
    config_data = copy.deepcopy(VALID_SQLITE_CONFIG)
    del config_data["SQLITE"]
    ini_file = create_ini_file(tmp_path, config_data)
    config = Config.load_config(str(ini_file))
    assert config.db.type == "sqlite", "DB_Type should be sqlite"
    assert config.db.name == "sqlite_db", "DB_Name should be sqlite_db"
    assert config.db.dir == "sqlite_data", "DB_Dir should be sqlite_data"

def test_missing_postgresql_section(tmp_path):
    config_data = VALID_POSTGRESQL_CONFIG.copy()
    del config_data["POSTGRESQL"]
    ini_file = create_ini_file(tmp_path, config_data)
    config = Config.load_config(str(ini_file))
    assert config.db.type == "postgresql", f"DB_Type should be postgresql, got {config.db.type}"
    assert config.db.name == "postgres_db", f"DB_Name should be postgres_db, got {config.db.name}"
    assert config.db.dir is None, f"DB_Dir should not exist, got {config.db.dir}"
    assert config.db.user == "postgres", f"DB_User should be postgres, got {config.db.user}"
    assert config.db.password == "Postgres123!", f"DB_Password should be Postgres123!, got {config.db.password}"
    assert config.db.host == "localhost", f"DB_Host should be localhost, got {config.db.host}"
    assert config.db.port == 5432, f"DB_Port should be 5432, got {config.db.port}"

@pytest.mark.parametrize("section, field", [
    ("GLOBAL", "ENV_MODE"),
    ("GLOBAL", "PORT"),
    ("GLOBAL", "LOG_LEVEL"),
    ("GLOBAL", "DEBUG"),
    ("GLOBAL", "SECRET_KEY"),
    ("DATABASE", "DB_TYPE"),
    ("DATABASE", "DB_NAME"),
    ("USER", "DEFAULT_ROLE"),
    ("AI", "DEFAULT_PROVIDER"),
    ("AI", "DEFAULT_MODEL"),
    ("AI", "API_KEY"),
])
def test_missing_fields(tmp_path, section, field):
    config_data = copy.deepcopy(VALID_SQLITE_CONFIG)
    del config_data[section][field]
    ini_file = create_ini_file(tmp_path, config_data)
    
    config = Config.load_config(str(ini_file))

    if section == "GLOBAL":
        section_config = config.global_
        config_class = GlobalConfig
    elif section == "DATABASE":
        section_config = config.db
        config_class = DatabaseConfig
    elif section == "USER":
        section_config = config.user
        config_class = UserConfig
    elif section == "AI":
        section_config = config.ai
        config_class = AIConfig
    
    field_name = field.split("_")[-1].lower()

    # Map the field names to their actual names in the Pydantic models
    field_name_map = {
        "GLOBAL": {
            "mode": "env",
            "port": "port",
            "level": "log_level",
            "debug": "debug",
            "key": "secret"
        },
        "DATABASE": {
            "type": "type",
            "name": "name",
            "dir": "dir",
            "user": "user",
            "password": "password",
            "host": "host",
            "port": "port"
        },
        "USER": {
            "role": "default_role"
        },
        "AI": {
            "provider": "default_provider",
            "model": "default_model",
            "key": "api_key"
        }
    }

    actual_field_name = field_name_map[section].get(field_name, field_name)

    actual_value = getattr(section_config, actual_field_name)

    expected_value = config_class.model_fields[actual_field_name].default

    assert actual_value == expected_value, f"Expected {expected_value}, got {actual_value}"


@pytest.mark.parametrize("section, field", [
    ("DATABASE", "DB_NAME"),
    ("SQLITE", "DB_DIR"),
])
def test_empty_strings_sqlite(tmp_path, section, field):
    config_data = copy.deepcopy(VALID_SQLITE_CONFIG)
    config_data[section][field] = ""
    ini_file = create_ini_file(tmp_path, config_data)
    config = Config.load_config(str(ini_file))
    if section == "DATABASE":
        assert config.db.name == "app", f"DB_NAME should be app and got {config.db.name}"
    elif section == "SQLITE":
        assert config.db.dir == "sqlite_data", f"DB_DIR should be sqlite_data and got {config.db.dir}"

@pytest.mark.parametrize("section, field", [
    ("DATABASE", "DB_NAME"),
    ("POSTGRESQL", "DB_USER"),
    ("POSTGRESQL", "DB_PASSWORD"),
    ("POSTGRESQL", "DB_HOST"),
    ("POSTGRESQL", "DB_PORT"),
])
def test_empty_strings_postgresql(tmp_path, section, field):
    config_data = VALID_POSTGRESQL_CONFIG.copy()
    config_data[section][field] = ""
    ini_file = create_ini_file(tmp_path, config_data)
    config = Config.load_config(str(ini_file))
    db_defaults = CONFIG_DEFAULTS["DB_TYPES"]["POSTGRESQL"]
    if section == "DATABASE":
        assert config.db.name == "app", f"DB_NAME should be app and got {config.db.name}"
    elif section == "POSTGRESQL":
        if field == "DB_USER":
            assert config.db.user == db_defaults["DB_USER"], f"DB_USER should be {db_defaults['DB_USER']} and got {config.db.user}"
        elif field == "DB_PASSWORD":
            assert config.db.password == db_defaults["DB_PASSWORD"], f"DB_PASSWORD should be {db_defaults['DB_PASSWORD']} and got {config.db.password}"
        elif field == "DB_HOST":
            assert config.db.host == db_defaults["DB_HOST"], f"DB_HOST should be {db_defaults['DB_HOST']} and got {config.db.host}"
        elif field == "DB_PORT":
            assert config.db.port == db_defaults["DB_PORT"], f"DB_PORT should be {db_defaults['DB_PORT']} and got {config.db.port}"

def test_invalid_port_string(tmp_path):
    config_data = copy.deepcopy(VALID_SQLITE_CONFIG)
    config_data["GLOBAL"]["PORT"] = "abc"
    ini_file = create_ini_file(tmp_path, config_data)
    with pytest.raises(ValueError, match="valid integer"):
        Config.load_config(str(ini_file))

def test_invalid_port_int(tmp_path):
    config_data = VALID_POSTGRESQL_CONFIG.copy()
    config_data["GLOBAL"]["PORT"] = "1010"
    config_data["POSTGRESQL"]["DB_PORT"] = "1010"
    ini_file = create_ini_file(tmp_path, config_data)
    config = Config.load_config(str(ini_file))
    assert config.global_.port == 1010
    assert config.db.port == 1010

def test_invalid_debug_type(tmp_path):
    config_data = copy.deepcopy(VALID_SQLITE_CONFIG)
    config_data["GLOBAL"]["DEBUG"] = "maybe"
    ini_file = create_ini_file(tmp_path, config_data)
    with pytest.raises(ValueError, match="valid boolean"):
        Config.load_config(str(ini_file))

def test_extra_fields(tmp_path):
    config_data = copy.deepcopy(VALID_SQLITE_CONFIG)
    config_data["GLOBAL"]["EXTRA"] = "value"
    ini_file = create_ini_file(tmp_path, config_data)
    config = Config.load_config(str(ini_file))
    assert config.global_.env == "development"
    assert "EXTRA" not in config.global_.__dict__

def test_empty_file(tmp_path):
    ini_file = tmp_path /"empty.ini"
    ini_file.touch()
    config = Config.load_config(str(ini_file))
    assert config.db.type == "sqlite"
    assert config.db.name == "app"
    assert config.db.dir == "sqlite_data"
    assert config.user.default_role == "viewer"

def test_non_existent_file():
    config = Config.load_config()
    assert config.db.type == "sqlite", "Default DB type should be sqlite"
    assert config.db.name == "app", "Default DB name should be app"
    assert config.db.dir == "sqlite_data", "Default DB dir should be sqlite_data"
    assert config.user.default_role == "viewer", "Default user role should be viewer"

def test_minimal_valid_config_sqlite(tmp_path):
    minimal_config = {
        "GLOBAL": {
            "ENV_MODE": "dev",
            "PORT": 80,
            "LOG_LEVEL": "debug",
            "DEBUG": False,
            "SECRET_KEY": "we3lyTeUaI7sBUGvNqCWFSOxNbnLYww2sfqK35t_ifx8cWbjV-J0vgz6mOLfQZKR1suGzTY1-YKwSQtPdQntSg"
        },
        "DATABASE": {
            "DB_TYPE": "sqlite",
            "DB_NAME": "db"
        },
        "SQLITE": {
            "DB_DIR": "."
        },
        "USER": {
            "DEFAULT_ROLE": "viewer"
        },
        "AI": {
            "DEFAULT_PROVIDER": "provider",
            "DEFAULT_MODEL": "model",
            "API_KEY": "key"
        }
    }
    ini_file = create_ini_file(tmp_path, minimal_config)
    config = Config.load_config(str(ini_file))
    assert config.global_.env == "dev", "ENV_MODE should be 'dev'"
    assert config.db.type == "sqlite", "DB_TYPE should be 'sqlite'"
    assert config.db.name == "db", "DB_NAME should be 'db'"
    assert config.db.dir == ".", "DB_DIR should be '.'"

def test_case_insensitive_sections(tmp_path):
    config_data = {
        "global": VALID_SQLITE_CONFIG["GLOBAL"],
        "database": VALID_SQLITE_CONFIG["DATABASE"],
        "sqlite": VALID_SQLITE_CONFIG["SQLITE"],
        "user": VALID_SQLITE_CONFIG["USER"],
        "ai": VALID_SQLITE_CONFIG["AI"]
    }
    ini_file = create_ini_file(tmp_path, config_data)

    config = Config.load_config(str(ini_file))
    print(f"CONFIG RETURN: {config}")
    assert config is not None, "Config should not be None"
    assert config.global_.env == "development", "Global: Env should be development"
    assert config.global_.port == 5000, "Global: Port should be 5000"
    assert config.global_.log_level == "info", "Global: Log Level should be info"
    assert config.global_.debug == True, "Global: Debug should be True"
    assert config.global_.secret == "CZ4WaeAaJYlU7lPtDBXQ11BFKOAl1ifWh9sgUx_URdVG6O4wz0yWQP2xgoxLA8B30zIkkhqsGant5QVNPWd6kA", "Global: Secrete should be valid"
    assert config.db.type == "sqlite", "Database: Type should be sqlite"
    assert config.db.name == "sqlite_db", "Database: Name should be sqlite_db"
    assert config.db.dir == "sqlite_data", "Database: Dir should be sqlite_data"
    assert config.user.default_role == "viewer", "User: Default role should be viewer"
    assert config.ai.default_provider == "xai", "AI: Default provider should be xai"
    assert config.ai.default_model == "grok-2-1212", "AI: Default model should be grok-2-1212"
    assert config.ai.api_key == "secret_key123", "AI: API key should be secret_key123"