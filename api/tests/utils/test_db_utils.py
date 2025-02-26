# test_db_utils.py

import pytest
import os
import alembic.config
from sqlalchemy.exc import OperationalError
from unittest.mock import patch

from app.utils.db_utils import db_manager

# Set up a test database path
TEST_DB_PATH = "test_database.db"

# Fixture to set up the test database environment
@pytest.fixture(scope="module")
def test_db():
    # Set environment variables for the test
    os.environ['DB_ENGINE'] = 'sqlite'
    os.environ['DB_DIR'] = os.path.dirname(os.path.abspath(__file__))
    os.environ['DB_NAME'] = os.path.splitext(TEST_DB_PATH)[0]

    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))

    # Run Alembic migrations to create the schema
    alembic_cfg = alembic.config.Config(os.path.join(app_dir, "alembic.ini"))
    alembic.command.upgrade(alembic_cfg, "head")

    yield db_manager

    # Clean up the test database
    db_manager.engine.dispose()
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), TEST_DB_PATH)
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

def test_database_connection(test_db):
    with test_db.get_db() as db:
        try:
            # Attempt to execute a simple query
            db.execute("SELECT 1")
        except OperationalError as e:
            pytest.fail(f"Database connection failed: {str(e)}")

def test_get_db_yields_session(test_db):
    with test_db.get_db() as db:
        assert not db.is_closed()
    
    # Check that the session is closed after the context manager
    assert db.is_closed()

def test_get_db_closes_session_on_exception(test_db):
    try:
        with test_db.get_db() as db:
            raise Exception("Test exception")
    except Exception:
        pass
    
    assert db.is_closed()

def test_database_url_construction():
    with patch.dict(os.environ, {
        'DB_ENGINE': 'sqlite',
        'DB_DIR': os.path.dirname(os.path.abspath(__file__)),
        'DB_NAME': 'test_db'
    }, clear=True):
        expected_url = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_db.db')}"
        assert db_manager.db_url == expected_url

def test_database_url_default_values():
    with patch.dict(os.environ, {'DB_ENGINE': 'sqlite'}, clear=True):
        expected_url = f"sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'test.db')}"
        assert db_manager.db_url == expected_url

if __name__ == '__main__':
    pytest.main([__file__])