import os
import json
import pytest
import shutil
import subprocess
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError

from app.utils.db_utils import DatabaseManager, db_manager
from app import PROJECT_ROOT, API_ROOT


class TestDatabaseManager:
    """Tests for the DatabaseManager class in db_utils.py"""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing"""
        with patch.dict(os.environ, {
            'DB_ENGINE': 'sqlite',
            'ENV_MODE': 'test',
            'DB_DIR': 'test_data',
            'DB_NAME': 'test_db'
        }):
            yield

    @pytest.fixture
    def db_manager_instance(self, mock_env_vars):
        """Create an isolated test instance of DatabaseManager"""
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()
            yield manager
            if manager.engine:
                manager.engine.dispose()

    @pytest.fixture
    def mock_postgres_env(self):
        """Mock PostgreSQL environment variables"""
        with patch.dict(os.environ, {
            'DB_ENGINE': 'postgresql',
            'ENV_MODE': 'test',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password',
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'test_db'
        }):
            yield

    def test_init(self, db_manager_instance):
        """Test the initialization of DatabaseManager"""
        assert db_manager_instance.db_engine == 'sqlite'
        assert db_manager_instance.mode == 'test'
        assert db_manager_instance.db_name.startswith('test_db_')
        assert db_manager_instance.db_name.endswith('_test')
        assert db_manager_instance.engine is None
        assert db_manager_instance.SessionLocal is None

    def test_init_with_postgres(self):
        """Test initialization with PostgreSQL engine"""
        with patch.dict(os.environ, {'DB_ENGINE': 'postgresql'}):
            with patch('app.utils.db_utils.load_dotenv'):
                manager = DatabaseManager()
                assert manager.db_engine == 'postgresql'
                assert hasattr(manager, 'postgres_user')
                assert hasattr(manager, 'postgres_password')
                assert hasattr(manager, 'postgres_host')
                assert hasattr(manager, 'postgres_port')

    def test_init_with_invalid_engine(self):
        """Test initialization with invalid engine raises ValueError"""
        with patch.dict(os.environ, {'DB_ENGINE': 'invalid_engine'}):
            with patch('app.utils.db_utils.load_dotenv'):
                with pytest.raises(ValueError, match="Invalid database engine"):
                    DatabaseManager()

    def test_get_package_name(self, db_manager_instance):
        mock_json_content = '{"name": "test-package"}'

        with patch("builtins.open", mock_open(read_data=mock_json_content)):
            package_name = db_manager_instance._get_package_name()
            assert package_name == "test-package"

        # For scoped packages, correctly extract the package name
        mock_json_content = '{"name": "@scope/test-package"}'
        with patch("builtins.open", mock_open(read_data=mock_json_content)):
            package_name = db_manager_instance._get_package_name()
            assert package_name == "test-package"

        # Test when package.json doesn't exist
        with patch("builtins.open", side_effect=FileNotFoundError):
            package_name = db_manager_instance._get_package_name()
            assert package_name is None

    def test_get_alembic_config(self, db_manager_instance):
        """Test _get_alembic_config method"""
        with patch('app.utils.db_utils.Config') as mock_config:
            mock_config.return_value = "mock_config"
            config = db_manager_instance._get_alembic_config()
            mock_config.assert_called_once_with(os.path.join(API_ROOT, "alembic.ini"))
            assert config == "mock_config"

    def test_get_alembic_version(self, db_manager_instance):
        """Test _get_alembic_version method"""
        mock_script = MagicMock()
        mock_script.get_current_head.return_value = "abc123"

        with patch('app.utils.db_utils.ScriptDirectory') as mock_script_dir:
            mock_script_dir.from_config.return_value = mock_script
            version = db_manager_instance._get_alembic_version()
            mock_script_dir.from_config.assert_called_once_with(db_manager_instance.alembic_cfg)
            assert version == "abc123"

    def test_set_db_name(self, db_manager_instance):
        """Test _set_db_name method with different configurations"""
        # Test with DB_NAME env var
        with patch.dict(os.environ, {"DB_NAME": "env_db_name"}):
            with patch.object(db_manager_instance, "_get_package_name", return_value=None):
                db_name = db_manager_instance._set_db_name()
                assert "env_db_name" in db_name

        with patch.dict(os.environ, {"DB_NAME": ""}):
            with patch.object(db_manager_instance, "_get_package_name", return_value="pkg_name"):
                db_name = db_manager_instance._set_db_name()
                assert "pkg_name" in db_name

        with patch.dict(os.environ, {"DB_NAME": ""}):
            with patch.object(db_manager_instance, "_get_package_name", return_value=None):
                db_name = db_manager_instance._set_db_name()
                assert "app" in db_name

    def test_set_db_dir(self, db_manager_instance):
        with patch.dict(os.environ, {"DB_DIR": "relative/path"}):
            db_dir = db_manager_instance._set_db_dir()
            assert db_dir == os.path.join(API_ROOT, "relative/path")

        abs_path = "/absolute/path"
        with patch('os.path.isabs', return_value=True):
            with patch.dict(os.environ, {"DB_DIR": abs_path}):
                db_dir = db_manager_instance._set_db_dir()
                assert db_dir == abs_path

    def test_build_db_url_sqlite(self, db_manager_instance):
        with patch.dict(os.environ, {"DB_DIR": "test_data"}):
            db_manager_instance.db_name = "test_db"
            db_manager_instance.db_dir = os.path.join(API_ROOT, "test_data")
            url = db_manager_instance._build_db_url()
            assert url.startswith("sqlite:///")
            assert "test_data" in url
            assert "test_db.db" in url

    def test_build_db_url_postgres(self, mock_postgres_env):
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()
            url = manager._build_db_url()
            assert url.startswith("postgresql://")
            assert "test_user:test_password@localhost:5432/test_db" in url

    def test_connect(self, db_manager_instance):
        with patch('app.utils.db_utils.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            db_manager_instance.db_engine = "sqlite"
            db_manager_instance.db_url = "sqlite:///test_path/test_db.db"

            with patch('os.makedirs') as mock_makedirs:
                engine = db_manager_instance._connect()
                mock_makedirs.assert_called_once_with(os.path.dirname("test_path/test_db.db"), exist_ok=True)
                mock_create_engine.assert_called_once_with(db_manager_instance.db_url)
                assert engine == mock_engine

    def test_create_postgresql_db_exists(self, mock_postgres_env):
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1  # DB exists
        mock_conn.execute.return_value = mock_result

        with patch('app.utils.db_utils.create_engine', return_value=mock_engine):
            with patch.object(mock_engine, 'connect', return_value=mock_conn):
                created = manager._create_postgresql_db()
                assert not created  # Should return False as DB already exists
                mock_conn.execute.assert_any_call(text(f"SELECT 1 FROM pg_database WHERE datname = '{manager.db_name}'"))
                assert not any("CREATE DATABASE" in str(call) for call in mock_conn.execute.call_args_list)

    def test_create_postgresql_db_new(self, mock_postgres_env):
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None  # DB doesn't exist
        mock_conn.execute.return_value = mock_result

        with patch('app.utils.db_utils.create_engine', return_value=mock_engine):
            with patch.object(mock_engine, 'connect', return_value=mock_conn):
                created = manager._create_postgresql_db()
                assert created  # Should return True as new DB created
                mock_conn.execute.assert_any_call(text(f"SELECT 1 FROM pg_database WHERE datname = '{manager.db_name}'"))
                mock_conn.execute.assert_any_call(text('CREATE DATABASE "' + manager.db_name + '"'))
    def test_run_migrations(self, db_manager_instance):
        with patch('app.utils.db_utils.command') as mock_command:
            db_manager_instance.db_url = "test_url"
            db_manager_instance.alembic_cfg = MagicMock()
            db_manager_instance._run_migrations()
            db_manager_instance.alembic_cfg.set_main_option.assert_called_once_with(
                "sqlalchemy.url", "test_url")
            mock_command.upgrade.assert_called_once_with(db_manager_instance.alembic_cfg, "head")

    def test_get_db(self, db_manager_instance):
        mock_session = MagicMock()
        mock_session_local = MagicMock(return_value=mock_session)

        db_manager_instance.SessionLocal = mock_session_local

        with patch.object(db_manager_instance, '_connect'):
            session_generator = db_manager_instance.get_db()
            db = next(session_generator)

            assert db == mock_session
            try:
                next(session_generator)
                assert False, "Generator should have only one value"
            except StopIteration:
                pass
            mock_session.close.assert_called_once()

    def test_get_db_no_session_local(self, db_manager_instance):
        mock_session = MagicMock()
        mock_session_local = MagicMock(return_value=mock_session)

        db_manager_instance.SessionLocal = None

        with patch.object(db_manager_instance, '_connect'):
            with patch.object(db_manager_instance, 'SessionLocal', mock_session_local):
                session_generator = db_manager_instance.get_db()
                db = next(session_generator)
                assert db == mock_session

    def test_setup_db_sqlite(self, db_manager_instance):
        mock_engine = MagicMock()
        mock_sessionmaker = MagicMock()

        with patch('os.makedirs') as mock_makedirs:
            with patch.object(db_manager_instance, '_connect', return_value=mock_engine):
                with patch('app.utils.db_utils.sessionmaker', return_value=mock_sessionmaker):
                    with patch.object(db_manager_instance, '_run_migrations'):
                        db_manager_instance.db_engine = "sqlite"
                        db_manager_instance.db_url = "sqlite:///test_path/test_db.db"

                        result = db_manager_instance.setup_db()

                        mock_makedirs.assert_called_once_with(os.path.dirname("test_path/test_db.db"), exist_ok=True)
                        assert db_manager_instance.engine == mock_engine
                        assert db_manager_instance.SessionLocal == mock_sessionmaker
                        assert result == db_manager_instance

    def test_setup_db_postgres(self, mock_postgres_env):
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()

        mock_engine = MagicMock()
        mock_sessionmaker = MagicMock()

        with patch.object(manager, '_create_postgresql_db') as mock_create_db:
            with patch.object(manager, '_connect', return_value=mock_engine):
                with patch('app.utils.db_utils.sessionmaker', return_value=mock_sessionmaker):
                    with patch.object(manager, '_run_migrations'):
                        result = manager.setup_db()

                        mock_create_db.assert_called_once()
                        assert manager.engine == mock_engine
                        assert manager.SessionLocal == mock_sessionmaker
                        assert result == manager

    def test_setup_db_migration_error(self, db_manager_instance):
        mock_engine = MagicMock()

        with patch('os.makedirs'):
            with patch.object(db_manager_instance, '_connect', return_value=mock_engine):
                with patch('app.utils.db_utils.sessionmaker'):
                    with patch.object(db_manager_instance, '_run_migrations', side_effect=Exception("Migration error")):
                        result = db_manager_instance.setup_db()
                assert result == db_manager_instance

    @pytest.mark.asyncio
    async def test_get_async_db(self, db_manager_instance):
        mock_session = MagicMock()
        db_manager_instance.SessionLocal = MagicMock(return_value=mock_session)

        async for session in db_manager_instance.get_async_db():
            assert session == mock_session

        mock_session.close.assert_called_once()

    def test_drop_db_sqlite(self, db_manager_instance):
        mock_engine = MagicMock()
        db_manager_instance.engine = mock_engine
        db_manager_instance.db_engine = "sqlite"
        db_manager_instance.db_file = "test_file.db"

        with patch('os.path.exists', return_value=True):
            with patch('os.remove') as mock_remove:
                result = db_manager_instance.drop_db()

                mock_engine.dispose.assert_called_once()
                mock_remove.assert_called_once_with("test_file.db")
                assert db_manager_instance.engine is None
                assert db_manager_instance.SessionLocal is None
                assert result == db_manager_instance

    def test_drop_db_postgres(self, mock_postgres_env):
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()

        mock_engine = MagicMock()
        manager.engine = mock_engine

        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1  # DB exists
        mock_conn.execute.return_value = mock_result

        with patch('app.utils.db_utils.create_engine') as mock_create_engine:
            mock_default_engine = MagicMock()
            mock_create_engine.return_value = mock_default_engine
            with patch.object(mock_default_engine, 'connect', return_value=mock_conn):
                result = manager.drop_db()

                mock_engine.dispose.assert_called_once()
                mock_conn.execute.assert_any_call(text(f"SELECT 1 FROM pg_database WHERE datname = '{manager.db_name}'"))
                assert any("pg_terminate_backend" in str(call) for call in mock_conn.execute.call_args_list)
                mock_conn.execute.assert_any_call(text("COMMIT"))
                mock_conn.execute.assert_any_call(text('DROP DATABASE "' + manager.db_name + '"'))
                assert manager.engine is None
                assert manager.SessionLocal is None
                assert result == manager

    def test_test_connection_success(self, db_manager_instance):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        db_manager_instance.db_engine = "test_engine"
        db_manager_instance.db_name = "test_db"

        with patch.object(db_manager_instance, '_connect', return_value=mock_engine):
            with patch.object(mock_engine, 'connect', return_value=mock_conn):
                with patch.object(mock_conn, '__enter__', return_value=mock_conn):
                    with patch.object(mock_conn, '__exit__'):
                        result = db_manager_instance.test_connection()

                        assert result["success"] is True
                        assert result["engine"] == "test_engine"
                        assert result["database"] == "test_db"
                        assert result["message"] == "Connection successful"
                        mock_conn.execute.assert_called_once_with(text("SELECT 1"))

    def test_test_connection_failure(self, db_manager_instance):
        mock_engine = MagicMock()
        db_manager_instance.db_engine = "test_engine"
        db_manager_instance.db_name = "test_db"

        error = OperationalError("statement", "params", "orig")

        with patch.object(db_manager_instance, '_connect', return_value=mock_engine):
            with patch.object(mock_engine, 'connect', side_effect=error):
                result = db_manager_instance.test_connection()

                assert result["success"] is False
                assert result["engine"] == "test_engine"
                assert result["database"] == "test_db"
                assert str(error) in result["message"]

    def test_purge_data(self, db_manager_instance):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["table1", "table2", "alembic_version"]
        db_manager_instance.db_engine = "sqlite"

        with patch('app.utils.db_utils.inspect', return_value=mock_inspector):
            with patch.object(db_manager_instance, '_connect', return_value=mock_engine):
                with patch.object(mock_engine, 'begin', return_value=mock_conn):
                    with patch.object(mock_conn, '__enter__', return_value=mock_conn):
                        with patch.object(mock_conn, '__exit__'):
                            result = db_manager_instance.purge_data()

                            mock_conn.execute.assert_any_call(text("PRAGMA foreign_keys = OFF;"))
                            mock_conn.execute.assert_any_call(text("DELETE FROM table1"))
                            mock_conn.execute.assert_any_call(text("DELETE FROM table2"))
                            mock_conn.execute.assert_any_call(text("PRAGMA foreign_keys = ON;"))

                            assert result is True

    def test_purge_data_postgres(self, mock_postgres_env):
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["table1", "table2", "alembic_version"]

        with patch('app.utils.db_utils.inspect', return_value=mock_inspector):
            with patch.object(manager, '_connect', return_value=mock_engine):
                with patch.object(mock_engine, 'begin', return_value=mock_conn):
                    with patch.object(mock_conn, '__enter__', return_value=mock_conn):
                        with patch.object(mock_conn, '__exit__'):
                            result = manager.purge_data()
                            assert result is True

    def test_purge_data_with_exclude(self, db_manager_instance):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["table1", "table2", "table3", "alembic_version"]
        db_manager_instance.db_engine = "sqlite"

        with patch('app.utils.db_utils.inspect', return_value=mock_inspector):
            with patch.object(db_manager_instance, '_connect', return_value=mock_engine):
                with patch.object(mock_engine, 'begin', return_value=mock_conn):
                    with patch.object(mock_conn, '__enter__', return_value=mock_conn):
                        with patch.object(mock_conn, '__exit__'):
                                result = db_manager_instance.purge_data(exclude_tables=["table2"])

                                mock_conn.execute.assert_any_call(text("PRAGMA foreign_keys = OFF;"))
                                mock_conn.execute.assert_any_call(text("DELETE FROM table1"))
                                mock_conn.execute.assert_any_call(text("DELETE FROM table3"))
                                assert not any("DELETE FROM table2" in str(call) for call in mock_conn.execute.call_args_list)
                                mock_conn.execute.assert_any_call(text("PRAGMA foreign_keys = ON;"))

                                assert result is True

    def test_backup_db_sqlite(self, db_manager_instance):
        db_manager_instance.db_engine = "sqlite"
        db_manager_instance.db_name = "test_db"
        db_manager_instance.db_file = "/path/to/test_db.db"
        db_manager_instance.db_dir = "/path/to"

        mock_timestamp = "20230101_120000"
        expected_backup_path = "/path/to/backups/test_db_20230101_120000.db"

        with patch('os.path.exists', return_value=True):
            with patch('os.makedirs') as mock_makedirs:
                with patch('shutil.copy2') as mock_copy:
                    with patch('datetime.datetime') as mock_datetime:
                        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
                        mock_datetime.strftime = datetime.strftime
                        result = db_manager_instance.backup_db()

                        mock_makedirs.assert_called_once_with(os.path.join("/path/to", "backups"), exist_ok=True)
                        mock_copy.assert_called_once_with("/path/to/test_db.db", expected_backup_path)
                        assert result is True

    def test_backup_db_postgres(self, mock_postgres_env):
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()

        manager.db_name = "test_db"
        manager.db_dir = "/path/to"

        expected_backup_path = "/path/to/backups/test_db_20230101_120000.sql"

        with patch('os.makedirs') as mock_makedirs:
            with patch('os.system') as mock_system:
                with patch('datetime.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
                    mock_datetime.strftime = datetime.strftime

                    result = manager.backup_db()

                    mock_makedirs.assert_called_once_with(os.path.join("/path/to", "backups"), exist_ok=True)
                    mock_system.assert_called_once()
                    assert "pg_dump" in mock_system.call_args[0][0]
                    assert manager.db_name in mock_system.call_args[0][0]
                    assert result is True

    def test_backup_db_custom_path(self, db_manager_instance):
        db_manager_instance.db_engine = "sqlite"
        db_manager_instance.db_file = "/path/to/test_db.db"
        custom_backup_path = "/custom/backup/path/backup.db"

        with patch('os.path.exists', return_value=True):
            with patch('os.makedirs', return_value=True) as mock_makedirs:
                with patch('shutil.copy2') as mock_copy:
                    result = db_manager_instance.backup_db(backup_path=custom_backup_path)

                    mock_makedirs.assert_called_once_with(os.path.dirname(custom_backup_path), exist_ok=True)
                    mock_copy.assert_called_once_with("/path/to/test_db.db", custom_backup_path)
                    assert result is True

    def test_backup_db_sqlite_not_exists(self, db_manager_instance):
        db_manager_instance.db_engine = "sqlite"
        db_manager_instance.db_file = "/path/to/test_db.db"

        with patch('os.path.exists', return_value=False):
            result = db_manager_instance.backup_db()
            assert result is False

    def test_restore_db_sqlite(self, db_manager_instance):
        db_manager_instance.db_engine = "sqlite"
        db_manager_instance.db_file = "/path/to/test_db.db"
        backup_path = "/path/to/backup.db"

        with patch('os.path.exists', return_value=True):
            with patch('os.makedirs') as mock_makedirs:
                with patch('shutil.copy2') as mock_copy:
                    with patch.object(db_manager_instance, 'setup_db') as mock_setup:
                        result = db_manager_instance.restore_db(backup_path)

                        mock_makedirs.assert_called_once_with(os.path.dirname("/path/to/test_db.db"), exist_ok=True)
                        mock_copy.assert_called_once_with("/path/to/backup.db", "/path/to/test_db.db")
                        mock_setup.assert_called_once_with(run_migrations=False)
                        assert result is True

    def test_restore_db_postgres(self, mock_postgres_env):
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()

        backup_path = "/path/to/backup.sql"

        with patch.object(manager, 'drop_db') as mock_drop:
            with patch.object(manager, '_create_postgresql_db') as mock_create:
                with patch('os.system') as mock_system:
                    with patch.object(manager, 'setup_db') as mock_setup:
                        result = manager.restore_db(backup_path)

                        mock_drop.assert_called_once()
                        mock_create.assert_called_once()
                        mock_system.assert_called_once()
                        assert "psql" in mock_system.call_args[0][0]
                        assert manager.db_name in mock_system.call_args[0][0]
                        mock_setup.assert_called_once_with(run_migrations=False)
                        assert result is True

    def test_restore_db_sqlite_not_exists(self, db_manager_instance):
        db_manager_instance.db_engine = "sqlite"
        backup_path = "/path/to/backup.db"

        with patch('os.path.exists', return_value=False):
            result = db_manager_instance.restore_db(backup_path)
            assert result is False

    def test_backup_db_postgres(self, mock_postgres_env):
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()

        manager.db_name = "test_db"
        manager.db_dir = "/path/to"

        expected_backup_path = "/path/to/backups/test_db_20230101_120000.sql"

        with patch('os.makedirs') as mock_makedirs:
            with patch('subprocess.run') as mock_run:
                with patch('datetime.datetime') as mock_datetime:
                    mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
                    mock_datetime.strftime = datetime.strftime

                    mock_process = MagicMock()
                    mock_run.return_value = mock_process

                    result = manager.backup_db()

                    mock_makedirs.assert_called_once_with(os.path.join("/path/to", "backups"), exist_ok=True)
                    mock_run.assert_called_once()
                    args = mock_run.call_args[0][0]
                    assert "pg_dump" in args[0]
                    assert "--format" in args
                    assert "--file" in args
                    assert manager.db_name in args
                    assert result == expected_backup_path

    def test_purge_data(self, db_manager_instance):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["table1", "table2", "alembic_version"]

        db_manager_instance.db_file = "/path/to/test_db.db"
        custom_backup_path = "/custom/backup/path/backup.db"

        with patch('os.path.exists', return_value=True):
            with patch('shutil.copy2') as mock_copy:
                result = db_manager_instance.backup_db(backup_path=custom_backup_path)

                mock_copy.assert_called_once_with("/path/to/test_db.db", custom_backup_path)
                assert result == custom_backup_path

    def test_backup_db_sqlite_not_exists(self, db_manager_instance):
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_inspector = MagicMock()
        with patch('shutil.copy2') as mock_copy:
            custom_backup_path = "/custom/backup/path/backup.db"
            mock_copy.assert_called_once_with("/path/to/test_db.db", custom_backup_path)
            with patch('app.utils.db_utils.inspect', return_value=mock_inspector):
                with patch.object(db_manager_instance, '_connect', return_value=mock_engine):
                    with patch.object(mock_engine, 'begin', return_value=mock_conn):
                        with patch.object(mock_conn, '__enter__', return_value=mock_conn):
                            with patch.object(mock_conn, '__exit__'):
                                result = db_manager_instance.purge_data()

                                mock_conn.execute.assert_any_call(text("PRAGMA foreign_keys = OFF;"))
                                mock_conn.execute.assert_any_call(text("DELETE FROM table1"))
                                mock_conn.execute.assert_any_call(text("DELETE FROM table2"))
                                mock_conn.execute.assert_any_call(text("PRAGMA foreign_keys = ON;"))

                assert result == custom_backup_path

    def test_purge_data_postgres(self, mock_postgres_env):
        with patch('app.utils.db_utils.load_dotenv'):
            manager = DatabaseManager()

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["table1", "table2", "alembic_version"]

        with patch('app.utils.db_utils.inspect', return_value=mock_inspector):
            with patch.object(manager, '_connect', return_value=mock_engine):
                with patch.object(mock_engine, 'begin', return_value=mock_conn):
                    with patch.object(mock_conn, '__enter__', return_value=mock_conn):
                        with patch.object(mock_conn, '__exit__'):
                            result = manager.purge_data()
                            assert result is True

    def test_purge_data_with_exclude(self, db_manager_instance):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ["table1", "table2", "table3", "alembic_version"]
        db_manager_instance.db_engine = "sqlite"

        with patch('app.utils.db_utils.inspect', return_value=mock_inspector):
            with patch.object(db_manager_instance, '_connect', return_value=mock_engine):
    def test_backup_db_sqlite_not_exists(self, db_manager_instance):
                    with patch.object(mock_conn, '__enter__', return_value=mock_conn):
                        with patch.object(mock_conn, '__exit__'):
                                result = db_manager_instance.purge_data(exclude_tables=["table2"])

                                mock_conn.execute.assert_any_call(text("PRAGMA foreign_keys = OFF;"))
                                mock_conn.execute.assert_any_call(text("DELETE FROM table1"))
                                mock_conn.execute.assert_any_call(text("DELETE FROM table3"))
                                assert not any("DELETE FROM table2" in str(call) for call in mock_conn.execute.call_args_list)
                                mock_conn.execute.assert_any_call(text("PRAGMA foreign_keys = ON;"))

                                assert result is True

    def test_backup_db_sqlite(self, db_manager_instance):
        db_manager_instance.db_file = "/path/to/test_db.db"
        db_manager_instance.db_file = "/path/to/test_db.db"

        with patch('os.path.exists', return_value=False):
            with pytest.raises(FileNotFoundError):
                db_manager_instance.backup_db()

    def test_restore_db_sqlite(self, db_manager_instance):
        db_manager_instance.db_engine = "sqlite"
        db_manager_instance.db_name = "test_db"

        backup_path = "/path/to/backup.db"
        db_manager_instance.db_dir = "/path/to"

        mock_timestamp = "20230101_120000"
        expected_backup_path = "/path/to/backups/test_db_20230101_120000.db"

                        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
                        mock_datetime.strftime = datetime.strftime
                        result = db_manager_instance.backup_db()
                    with patch.object(db_manager_instance, 'setup_db') as mock_setup:
                        result = db_manager_instance.restore_db(backup_path)
                        mock_makedirs.assert_called_once_with(os.path.join("/path/to", "backups"), exist_ok=True)
                        mock_copy.assert_called_once_with("/path/to/test_db.db", expected_backup_path)
                        assert result is True
                        mock_makedirs.assert_
    def test_backup_db_postgres(self, mock_postgres_env):
            manager = DatabaseManager()

        manager.db_name = "test_db"
        manager.db_dir = "/path/to"

