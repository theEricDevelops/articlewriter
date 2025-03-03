import re, base64, os
from os import path
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError, ConfigDict, field_validator
from typing import Literal, Optional, Union, ClassVar, Any
from configparser import ConfigParser
from app.constants import *
import logging
from app.constants import API_ROOT, CONFIG_DEFAULTS

# Create a custom logger for configuration errors
class ConfigException(Exception):
    """
        Custom exception class for configuration errors.
    """
    def __init__(self, message: str) -> None:
        # Log the error message
        config_log.error(message)

        # Call the parent class constructor
        super().__init__(message)

# Custom exception classes for specific configuration errors
class ConfigValueError(ConfigException, ValueError):...
class ConfigValidationError(ConfigException, ValidationError):...
class ConfigFileError(ConfigException, FileNotFoundError):...
class ConfigFileNotFoundError(ConfigException, FileNotFoundError):...
class ConfigFilePermissionError(ConfigException, PermissionError):...
class ConfigFileReadError(ConfigException, PermissionError):...
class ConfigLogError(ConfigException, PermissionError):...

class ConfigLogger(logging.Logger):
    """
    Custom logger class for configuration logging.

    Args:
       name (str): The name of the logger.
        **kwargs (dict): Additional keyword arguments to pass to the logger constructor
           (e.g., level, format, etc.).

    Returns:
        None

    Raises:
        None
    """
    def __init__(self, name: str = "config", **kwargs: dict[str, Any]) -> None:
        """
        Initialize the logger with the given name and keyword arguments.
        """
        # Call the parent class constructor
        super().__init__(name)

        # Set the default values for the logger attributes
        self.setLevel(int(os.getenv("LOG_LEVEL", "0")))
        self.propagate = False
        self.formatter = logging.Formatter(
            fmt=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            datefmt=os.getenv("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S"),
        )
        self.fh = None

        # Check the kwargs for a log file path
        log_dir = kwargs.get("log_dir", os.getenv("LOG_DIR", API_ROOT + "/logs"))
        log_file = kwargs.get("log_file", os.getenv("LOG_FILE", os.path.join(log_dir, name)))
        log_path = os.path.join(log_dir, log_file + ".log")

        # Check if the log file path exists and is writable
        if not self._check_for_log_path(log_path):
            # Create the log file if it does not exist
            self._create_log_file(log_dir, log_path)

        # Add the file handler to the logger
        self.add_handler(log_path)
        self._create_log_header(log_path)

    def _check_for_log_path(self, log_path: str) -> bool:
        """
        Check if the log file path exists and is writable.

        Args:
            log_path (str): The path to the log file.

        Returns:
            bool: True if the log file path exists and is writable.

        Raises:
            ConfigFileNotFoundError: If the log file path does not exist.
            ConfigFilePermissionError: If the log file is not writable.
        """
        if Path(log_path).exists():
            if Path(log_path).is_file():
                if os.access(log_path, os.W_OK):
                    with open(log_path, "w") as log_file:
                        log_file.truncate(0)
                    return True
                else:
                    raise ConfigFilePermissionError(f"Log file is not writable: {log_path}")
            else:
                raise ConfigFileError(f"Log path is not a file: {log_path}")
        else:
            raise ConfigFileNotFoundError(f"Log file not found: {log_path}")

    def _create_log_file(self, log_dir: str, log_path: str) -> None:
        """
        Create the log file if it doesn't exist.

        Args:
            log_dir (str): The directory to create the log file in.
            log_path (str): The path to the log file.

        Returns:
            None

        Raises:
           ConfigFileError: If the log file could not be created.
        """
        try:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            Path(log_path).touch(exist_ok=True)
            
        except Exception as e:
            raise ConfigFileError("Failed to create log file: " + str(log_path) + ": " + str(e))

    def _configure_log(self, hdlr: logging.Handler) -> None:
        """
        Configure the logger with the given handler.

        Args:
            self (Logger): The logger object.
            hdlr (logging.Handler): The handler to configure.

        Returns:
           None

        Raises:
            ConfigError: If the logger could not be configured.
        """
        try:
            hdlr.setLevel(int(os.getenv("LOG_LEVEL", "0")))
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            hdlr.setFormatter(formatter)
        except Exception as e:
            raise ConfigLogError(f"Failed to configure logger: {e}")

    def _add_file_handler(self, log_path) -> logging.FileHandler:
        """
        Add a file handler to the logger.

        Args:
            log_path (str): The path to the log file.

        Returns:
            file_handler (logging.FileHandler): The file handler object.

        Raises:
           ConfigFileError: If the file handler cannot be created.
        """

        try:
            fh = logging.FileHandler(log_path)
            self._configure_log(fh)
            return fh

        except ConfigException as e:
            raise ConfigLogError(f"Failed to create file handler: {e}")

    def _add_stream_handler(self, log_path) -> logging.StreamHandler:
        """
        Add a stream handler to the logger.

        Args:
            log_path (str): The path to the log file.

        Returns:
            stream_handler (logging.StreamHandler): The stream handler object.

        Raises:
           ConfigLogError: If the stream handler cannot be created.
        """

        try:
            sh = logging.StreamHandler()
            self._configure_log(sh)
            return sh
        except ConfigException as e:
            raise ConfigLogError(f"Failed to create file handler: {e}")

    def _create_log_header(self, log_file: str) -> None:
        self.info("")
        self.info("----------------------------------------")
        self.info("Log file created and written to: %s", log_file)
        self.info("----------------------------------------")
        self.info("")

    def add_handler(self, log_path: str, type: str = "file") -> logging.Handler | logging.FileHandler | logging.StreamHandler:
        """
        Add a file handler to the logger.

        Args:
            log_file (str): The path to the log file.
            type (str): The type of handler to add. Defaults to "file".

        Returns:
           file_handler (logging.FileHandler): The file handler object. |
           stream_handler (logging.StreamHandler): The stream handler object. |
           handler (logging.Handler): The handler object.

        Raises:
           ConfigLogError: If the file handler cannot be created.
        """

        try:
            match type:
                case "file":
                    handler = self._add_file_handler(log_path)
                    if isinstance(handler, logging.FileHandler):
                        self.addHandler(handler)
                case "stream":
                    handler = self._add_stream_handler()
                    if isinstance(handler, logging.StreamHandler):
                        self.addHandler(handler)
                case _:
                    raise ConfigLogError(f"Invalid handler type: {type}")
            return handler
        except ConfigLogError as e:
            raise ConfigLogError(f"Failed to add handler: {e}")

    def error(self, message: str) -> None:
        logging.debug(message, exc_info=True)

# Set up the logger
config_log = ConfigLogger("config")

def validate_port(port: Union[str, int]) -> int:
    """
    Validate and convert a port number to an integer.
    The port number must be a valid integer between 1 and 65535.
    Args:
        port (Union[str, int]): The port number to validate.

    Returns:
        int: The validated port number as an integer.

    Raises:
        ConfigValueError: If the port is not a valid integer or out of range.
    """
    try:
        port_int = int(port)
    except ValueError:
        raise ConfigValueError(f"Invalid port number: {port}. Must be a valid integer.")

    if port_int < 1 or port_int > 65535:
        raise ConfigValueError(f"Port number {port_int} is out of valid range (1-65535).")

    return port_int

def validate_host(host: str) -> str:
    """
    Validate a host string.
    Args:
        host (str): The host string to validate.
    Returns:
        str: The validated host string.
    Raises:
        ConfigValueError: If the host is not a valid string.
    """
    hostname_regex = r'^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$'
    ip_regex = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'

    if re.match(hostname_regex, host):
        return host
    elif re.match(ip_regex, host):
        octets = host.split('.')
        if all(0 <= int(octet) <= 255 for octet in octets):
            return host
        else:
            raise ConfigValueError("Invalid IP address format.")
    else:
        raise ConfigValueError("Invalid hostname format.")

def validate_dir(dir: str) -> str:
    """
    Validate a directory path.
    Args:
        dir (str): The directory path to validate.
    Returns:
        str: The validated directory path.
    Raises:
        ConfigValueError: If the directory is not a valid string.
    """

    if not os.path.exists(dir):
        try:
            os.makedirs(dir)
        except OSError:
            raise ConfigValueError(f"Invalid directory path: {dir}. Directory does not exist and could not be created.")
    elif not os.path.isdir(dir):
            raise ConfigValueError(f"Invalid directory path: {dir}. Path exists but is not a directory.")
    elif not os.access(dir, os.W_OK):
        raise ConfigValueError(f"Invalid directory path: {dir}. Directory is not writable.")
    else:
        return dir

def validate_user(user: str) -> str:
    """
    Validate a user name.
    Args:
        user (str): The user name to validate.
    Returns:
        str: The validated user name.
    Raises:
        ConfigValueError: If the user name is not a valid string.
    """
    if not re.match(r'^[a-zA-Z0-9_]+$', user):
        raise ConfigValueError("DB_USER must contain only alphanumeric characters and underscores.")
    return user

def validate_password(password: str) -> str:
    """
    Validate a password.
    Args:
        password (str): The password to validate.
    Returns:
        str: The validated password.
    Raises:
        ConfigValueError: If the password is not a valid string.
    """
    # Check if the password meets certain complexity requirements
    if len(password) < 8:
        raise ConfigValueError("DB_PASSWORD must be at least 8 characters long")

    if not re.search(r'[A-Z]', password):
        raise ConfigValueError("DB_PASSWORD must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        raise ConfigValueError("DB_PASSWORD must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        raise ConfigValueError("DB_PASSWORD must contain at least one digit")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ConfigValueError("DB_PASSWORD must contain at least one special character")

    return password

def validate_secret(secret: str) -> str:
    """
    Validate a secret key for the application is a valid url-safe base64-encoded string.
    The secret key is used to sign cookies and other data that needs to be kept secure.
    Args:
        secret (str): The secret key to validate.
    Returns:
        str: The validated secret key.
    Raises:
        ConfigValueError: If the secret key is not a valid string.
    """
    if len(secret) < 32:
        raise ConfigValueError("SECRET_KEY must be at least 32 characters long")
    if not re.match(r'^[A-Za-z0-9_-]+$', secret):
        raise ConfigValueError("SECRET_KEY must be a valid url-safe base64-encoded string")
    if not base64.urlsafe_b64decode(secret + '==='):
        raise ConfigValueError("SECRET_KEY must be a valid url-safe base64-encoded string")
    if not re.search(r'[A-Z]', secret):
        raise ConfigValueError("SECRET_KEY must contain at least one uppercase letter")
    if not re.search(r'[a-z]', secret):
        raise ConfigValueError("SECRET_KEY must contain at least one lowercase letter")
    if not re.search(r'\d', secret):
        raise ConfigValueError("SECRET_KEY must contain at least one digit")

    return secret

class DatabaseConfig(BaseModel):
    type: Literal["sqlite", "postgresql", "postgres"] = Field(default="sqlite", alias="DB_TYPE")
    name: str = Field(default="app", min_length=1, alias="DB_NAME")
    dir: Optional[str] = Field(default=None, alias="DB_DIR")
    user: Optional[str] = Field(default=None, alias="DB_USER")
    password: Optional[str] = Field(default=None, alias="DB_PASSWORD")
    host: Optional[str] = Field(default=None, alias="DB_HOST")
    port: Optional[int] = Field(default=None, alias="DB_PORT")

    @field_validator('dir')
    @classmethod
    def validate_db_dir(cls, v):
        if v is None:
            return None
        return validate_dir(v)

    @field_validator('user')
    @classmethod
    def validate_db_user(cls, v):
        if v is None:
            return None
        return validate_user(v)

    @field_validator('password')
    @classmethod
    def validate_db_password(cls, v):
        if v is None:
            return None
        return validate_password(v)

    @field_validator('host')
    @classmethod
    def validate_db_host(cls, v):
        if v is None:
            return None

        return validate_host(v)

    @field_validator('port')
    @classmethod
    def validate_db_port(cls, v):
        if v is None:
            return None
        return validate_port(v)

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

# Global settings
class GlobalConfig(BaseModel):
    env: Literal["development", "dev", "production", "prod", "testing"] = Field(default="development", alias="ENV_MODE")
    port: Union[str, int] = Field(default=8000, alias="PORT")
    log_level: Literal["debug", "DEBUG", "info", "INFO", "warning", "WARNING", "error", "ERROR", "critical", "CRITICAL"] = Field(default="info", alias="LOG_LEVEL")
    debug: bool = Field(default=False, alias="DEBUG")
    secret: str = Field(default="default_insecure_key_01234567890_", min_length=32, alias="SECRET_KEY")

    @field_validator('port')
    @classmethod
    def validate_db_port(cls, v):
        if v is None:
            return None
        return validate_port(v)

    @field_validator('secret')
    @classmethod
    def validate_secret(cls, v):
        if v is None:
            return None
        return validate_secret(v)

# User settings
class UserConfig(BaseModel):
    default_role: Literal["admin", "editor", "viewer"] = Field(default="viewer", alias="DEFAULT_ROLE")

# AI settings
class AIConfig(BaseModel):
    default_provider: str = Field(default="xai", alias="DEFAULT_PROVIDER")
    default_model: str = Field(default="grok-2-1212", alias="DEFAULT_MODEL")
    api_key: str = Field(default="your_api_key", alias="API_KEY")

# Top-level config
class Config(BaseModel):
    global_: GlobalConfig = Field(default_factory=GlobalConfig, alias="GLOBAL")
    db: DatabaseConfig = Field(default_factory=DatabaseConfig, alias="DATABASE")
    user: UserConfig = Field(default_factory=UserConfig, alias="USER")
    ai: AIConfig = Field(default_factory=AIConfig, alias="AI")

    config_path: ClassVar[str] = f"{API_ROOT}/.env"
    model_config = ConfigDict(extra="forbid")

    @staticmethod
    def load_config(file_path: str = config_path) -> 'Config':
        """
            Load configuration from a file.

        Args:
            file_path: Path to the configuration file.
        
        Returns:
            Config object.
        """
        db_types = [alias for db_type in CONFIG_DEFAULTS["DB_TYPES"].values() for alias in db_type.get("ALIASES", [])]
        config_log.info(f"Loading configuration from: {file_path}")

        if not os.path.exists(file_path):
            config_log.debug(f"Configuration file not found: {file_path}")
        elif os.path.getsize(file_path) == 0:
            config_log.debug(f"Empty configuration file: {file_path}")

        parser = ConfigParser()
        parser.read(file_path)

        # Check if the configuration file is empty
        if not parser:
            config_log.error(f"Empty configuration file: {file_path}")

        config_dict = {section.upper(): {key.upper(): value for key, value in parser.items(section) if key.__len__() > 0 and value.__len__() > 0} for section in parser.sections() if section.__len__() > 0}
        config_log.debug(f"CONFIG_DICT: {config_dict}")

        # Set sqlite as the default if no DB_TYPE is specified
        db_config = config_dict.get("DATABASE", None)
        config_log.debug(f"DB_CONFIG: {db_config}")
        if db_config is None or db_config.get("DB_TYPE") is None:
            config_log.debug("No DB_TYPE specified, defaulting to sqlite")
            db_config = {"DB_TYPE": "sqlite"}
        elif db_config["DB_TYPE"].lower() not in db_types:
            config_log.debug(f"Unsupported DB_TYPE: {db_config['DB_TYPE']}")
            config_log.debug(f"Supported DB_TYPES: {CONFIG_DEFAULTS['DB_TYPES'].items()}")
            raise ConfigValueError(f"Unsupported DB_TYPE: {db_config['DB_TYPE']}")
        
        # Pull the DB Params from the config_dict and merge them with the defaults
        # depending on the DB_TYPE
        db_type = db_config["DB_TYPE"].lower()
        config_log.debug(f"DB_TYPE: {db_type}")

        # Get the default values for the specified DB_TYPE
        db_defaults = CONFIG_DEFAULTS["DB_TYPES"][db_type.upper()]
        config_log.debug(f"DB_DEFAULTS: {db_defaults}")

        # Get the DB Params from the config_dict
        db_params = config_dict.get(db_type.upper(), {})
        config_log.debug(f"DB_PARAMS: {db_params}")

        # Merge the configuration in the correct order:
        # 1. Defaults
        # 2. Database section from the config file
        # 3. Specific DB_TYPE section from the config file
        merged_config = {**db_defaults, **db_config, **db_params}
        config_log.debug(f"MERGED_CONFIG: {merged_config}")
        
        # Update the DATABASE section with the merged configuration
        config_dict["DATABASE"] = merged_config
        config_log.debug(f"Updated DATABASE section: {config_dict['DATABASE']}")

        # Remove the specific DB_TYPE section from the config_dict
        if db_type.upper() in config_dict:
            config_dict.pop(db_type.upper())
            config_log.debug(f"Removed {db_type.upper()} section from config_dict")

        valid_sections = [section.upper() for section in ["GLOBAL", "DATABASE", "USER", "AI"]]
        config_dict = {k: v for k, v in config_dict.items() if k in valid_sections}

        config_log.debug(f"Updated CONFIG_DICT: {config_dict}")

        config = Config(**config_dict)

        config_log.info(f"CONFIG: {config}")
        return config