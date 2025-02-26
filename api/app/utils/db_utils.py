import os, json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from alembic.script import ScriptDirectory
from alembic.config import Config
from alembic import command
from app.models import Base
from app.constants import PROJECT_ROOT, API_ROOT

class DatabaseManager:
    def __init__(self):
        # Load the .env file from the project root
        load_dotenv(dotenv_path=os.path.join(API_ROOT, ".env"))

        self.db_engine = os.getenv("DB_ENGINE", "sqlite")
        self.mode = os.getenv("ENV_MODE", "development")
        self.alembic_cfg = self._get_alembic_config()
        self.db_version = self._get_alembic_version()
        self.db_name = self._set_db_name()
        self.db_dir = self._set_db_dir()
        self.db_url = self._build_db_url()
        self.db_file = self.db_url.replace("sqlite:///", "") if self.db_engine == "sqlite" else None
        self.engine = None
        self.SessionLocal = None

        if self.db_engine not in ["sqlite", "postgresql", "postgres"]:
            raise ValueError("Invalid database engine. Use 'sqlite' or 'postgresql'")
        elif self.db_engine in ["postgresql", "postgres"]:
            # Store PostgreSQL connection parameters
            self.postgres_user = os.getenv("DB_USER", "postgres")
            self.postgres_password = os.getenv("DB_PASSWORD", "postgres") 
            self.postgres_host = os.getenv("DB_HOST", "localhost")
            self.postgres_port = os.getenv("DB_PORT", "5432")

    def _get_package_name(self):
        """Get the project name from the package.json file"""
        try:
            with open(os.path.join(PROJECT_ROOT, "package.json"), "r") as f:
                package_json = json.load(f)
                return package_json["name"]
            
                if name and "/" in name:
                    return name.split("/")[-1]
                return name
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
        
    def _get_alembic_config(self):
        """Get the alembic configuration from the alembic.ini file"""
        alembic_cfg = Config(os.path.join(API_ROOT, "alembic.ini"))
        return alembic_cfg

    def _get_alembic_version(self):
        """Get the current alembic version from the alembic_version file"""
        script = ScriptDirectory.from_config(self.alembic_cfg)
        current_version = script.get_current_head()

        return current_version

    def _set_db_name(self):
        """Set the database name based on environment variable or package.json file"""
        db_root = "app"
        db_version = self.db_version or None
        db_mode = self.mode or None

        # Start by getting the root of the db name
        if (os.getenv("DB_NAME")):
            db_root = os.getenv("DB_NAME")
        # If no DB_NAME is set, check the package.json file for the project name
        elif self._get_package_name() is not None:
            db_root = self._get_package_name()
        
        # Use the root, version, and mode to create the db name
        self.db_name = f"{db_root}_{db_version}_{db_mode}"
        return self.db_name

    def _set_db_dir(self):
        """Set the database directory based on environment variable or default"""
        # Check to see if the DB_DIR is relative or absolute
        if os.path.isabs(os.getenv("DB_DIR", "")):
            self.db_dir = os.getenv("DB_DIR")
        else:
            self.db_dir = os.path.join(API_ROOT, os.getenv("DB_DIR", "data"))
        return self.db_dir

    def _build_db_url(self):
        """ Build the database URL based on the environment variables or defaults """
        if self.db_engine == "sqlite":
            db_dir = os.getenv("DB_DIR", os.path.join(API_ROOT, "data"))
            db_data_path = os.path.join(db_dir, f"{self.db_name}.db")
            return f"sqlite:///{db_data_path}"
        else:
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "postgres")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")

            # For standard synchronous operations
            return f"{self.db_engine}://{db_user}:{db_password}@{db_host}:{db_port}/{self.db_name}"
    
    def _build_async_db_url(self):
        """Build the async database URL for PostgreSQL with asyncpg"""
        if self.db_engine in ["postgresql", "postgres"]:
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "postgres")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            
            return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{self.db_name}"
        return None

    def _connect(self):
        """Create and return a database engine connection"""
        # Ensure the directory exists for SQLite
        if self.db_engine == "sqlite":
            os.makedirs(self.db_file, exist_ok=True)
                    # Create the engine and return it
        engine = create_engine(self.db_url)
        return engine
    
    def _create_postgresql_db(self):
        """ Create a PostgreSQL database """
        db_created = False

        try:
            # Connect to default postgres database
            default_url = f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/postgres"
            default_engine = create_engine(default_url)
            
            with default_engine.connect() as conn:
                # Check if database exists
                result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{self.db_name}'"))
                exists = result.scalar() is not None
                
                if not exists:
                    # Exit transaction to allow CREATE DATABASE
                    conn.execute(text("COMMIT"))
                    conn.execute(text(f"CREATE DATABASE {self.db_name}"))
                    print(f"Database {self.db_name} created successfully")
                    db_created = True
                else:
                    print(f"Database {self.db_name} already exists")
                    
            default_engine.dispose()
            return db_created
        except Exception as e:
            print(f"Error creating database {self.db_name}: {e}")
            raise

    def _run_migrations(self):
        """Run the Alembic migrations to create the database tables"""
        self.alembic_cfg.set_main_option("sqlalchemy.url", self.db_url)
        command.upgrade(self.alembic_cfg, "head")

    def get_db(self):
        """Return a database session"""
        if not self.SessionLocal:
            self._connect()

        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def setup_db(self, run_migrations=True):
        """
        Create a new database.
        
        This method:
        1. Creates a new database if it doesn't exist
        2. Creates an engine and session factory
        3. Runs the alembic migrations to create the database tables, if needed
        4. Returns self for method chaining

        Args:
            run_migrations (bool): Whether to run alembic migrations. Default is True.

        Returns:
           DatabaseManager: Self instance for method chaining
        """
        if self.db_engine == "sqlite":
            os.makedirs(self.db_file, exist_ok=True)
        elif self.db_engine in ["postgresql", "postgres"]:
            # Create the database if it doesn't exist
            self._create_postgresql_db()
        
        self.engine = self._connect()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        if run_migrations:
            try:
                self._run_migrations()
            except Exception as e:
                print(f"Error running migrations: {e}")
                # Fallback to creating tables with SQLAlchemy
                Base.metadata.create_all(bind=self.engine)
        
        return self
    
    def setup_async_db(self):
        """
        Setup an async database for use with FastAPI
        
        Returns:
            DatabaseManager: Self instance for method chaining
        """
        if self.db_engine in ["postgresql", "postgres"]:
            async_url = self._build_async_db_url()
            if async_url:
                self.async_engine = create_async_engine(async_url)
                self.AsyncSessionLocal = sessionmaker(
                    class_=AsyncSession,
                    autocommit=False,
                    autoflush=False,
                    bind=self.async_engine
                )
                return self
        else:
            raise NotImplementedError("Async database setup is only supported for PostgreSQL")
        
    async def get_async_db(self):
        """
        Return an async database session
        
        Returns:
            AsyncSession: An async database session
        """
        if not self.AsyncSessionLocal:
            self.setup_async_db()
        
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    def validate_schema(self):
        """
        Validate the database schema against the models defined in SQLAlchemy.
        
        This checks if:
        - All tables defined in models exist in database
        - All columns defined in models exist in database
        - Column types match between models and database
        
        Returns:
            dict: Validation results including discrepancies found
        """
        from sqlalchemy import MetaData
        
        result = {
            "valid": True,
            "missing_tables": [],
            "missing_columns": {},
            "type_differences": {},
            "details": {}
        }
        
        try:
            if not self.engine:
                self.engine = self._connect()
                
            # Get actual database schema
            inspector = inspect(self.engine)
            db_tables = inspector.get_table_names()
            
            # Get expected schema from models
            metadata = Base.metadata
            model_tables = metadata.tables.keys()
            
            # Check for missing tables
            for table_name in model_tables:
                if table_name not in db_tables:
                    result["valid"] = False
                    result["missing_tables"].append(table_name)
            
            # Check columns for tables that exist
            for table_name in model_tables:
                if table_name in db_tables:
                    # Get model columns
                    model_table = metadata.tables[table_name]
                    model_columns = {col.name: col for col in model_table.columns}
                    
                    # Get database columns
                    db_columns = {col["name"]: col for col in inspector.get_columns(table_name)}
                    
                    # Check for missing columns
                    missing_columns = []
                    for col_name in model_columns:
                        if col_name not in db_columns:
                            missing_columns.append(col_name)
                    
                    if missing_columns:
                        result["valid"] = False
                        result["missing_columns"][table_name] = missing_columns
                    
                    # Check column types (this is simplified - full type checking is complex)
                    type_differences = []
                    for col_name, model_col in model_columns.items():
                        if col_name in db_columns:
                            db_col = db_columns[col_name]
                            # This is a simplified check - may need more sophisticated comparison
                            model_type = str(model_col.type)
                            db_type = str(db_col["type"])
                            
                            # Skip common differences in string representations
                            normalized_model_type = model_type.lower().replace('varchar', 'character varying')
                            normalized_db_type = db_type.lower().replace('varchar', 'character varying')
                            
                            if normalized_model_type != normalized_db_type:
                                type_differences.append({
                                    "column": col_name,
                                    "model_type": model_type,
                                    "db_type": db_type
                                })
                    
                    if type_differences:
                        result["valid"] = False
                        result["type_differences"][table_name] = type_differences
            
            return result
        except Exception as e:
            result["valid"] = False
            result["details"]["error"] = str(e)
            return result

    def drop_db(self):
        """
        Drop the database completely.

        This method:
        1. Drops the database if it exists
        2. Cleans up connections and resources
        3. Returns self for method chaining

        Returns:
            DatabaseManager: Self instance for method chaining
        """

        # Close any existing connections
        if self.engine:
            self.engine.dispose()
        
        # Handle database drop based on the engine
        if self.db_engine == "sqlite":
            
            if os.path.exists(self.db_file):
                os.remove(self.db_file)
                print(f"SQLite database {self.db_file} dropped successfully")
            else:
                print(f"SQLite database {self.db_file} does not exist")

        elif self.db_engine in ["postgresql", "postgres"]:
            try:
                # Connect to default postgres database
                default_url = f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/postgres"
                default_engine = create_engine(default_url)
                
                with default_engine.connect() as conn:
                    # Check if database exists
                    result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{self.db_name}'"))
                    exists = result.scalar() is not None
                    
                    if exists:
                        # Terminate connections
                        conn.execute(text(f"""
                            SELECT pg_terminate_backend(pg_stat_activity.pid)
                            FROM pg_stat_activity
                            WHERE pg_stat_activity.datname = '{self.db_name}'
                            AND pid <> pg_backend_pid()
                        """))
                        
                        # Drop database
                        conn.execute(text("COMMIT"))  # Exit transaction
                        conn.execute(text(f"DROP DATABASE {self.db_name}"))
                        print(f"Database {self.db_name} dropped successfully")
                    else:
                        print(f"Database {self.db_name} does not exist")
                        
                default_engine.dispose()
                
            except Exception as e:
                print(f"Error dropping database {self.db_name}: {e}")
                raise
        
        # Reset instance state
        self.engine = None
        self.SessionLocal = None
        
        return self
    
    def reset_db(self):
        """
        Reset the database by dropping it and recreating it with fresh tables.
        
        Returns:
            DatabaseManager: self instance for method chaining
        """

        self.drop_db()
        return self.setup_db(run_migrations=True)
    
    def test_connection(self):
        """
        Test the database connection and return status.
        
        Returns:
            dict: Connection status with details.
        """
        status = {
            "success": False,
            "engine": self.db_engine,
            "database": self.db_name,
            "message": "",
            "details": {}
        }

        try:
            if not self.engine:
                self.engine = self._connect()
            
            # Try a simple query to check the connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            status["success"] = True
            status["message"] = "Connection successful"
        except Exception as e:
            status["message"] = f"Connection failed: {e}"
            status["details"] = str(e)
        finally:
            if self.engine:
                self.engine.dispose()
        return status

    def purge_data(self, exclude_tables=None):
        """
        Remove all data from tables while preserving the schema.
        
        Args:
            exclude_tables (list, optional): Table names to exclude from purging
            
        Returns:
            DatabaseManager: Self instance for method chaining
        """
        if exclude_tables is None:
            exclude_tables = ['alembic_version']  # Always exclude alembic_version
        else:
            exclude_tables = list(exclude_tables) + ['alembic_version']
            
        try:
            if not self.engine:
                self.engine = self._connect()
            
            inspector = inspect(self.engine)
            all_tables = inspector.get_table_names()
            tables_to_purge = [table for table in all_tables if table not in exclude_tables]
            
            with self.engine.begin() as conn:
                # Disable foreign key checks for SQLite to allow deleting from tables with FK relationships
                if self.db_engine == "sqlite":
                    conn.execute(text("PRAGMA foreign_keys = OFF;"))
                
                # For PostgreSQL, we can use TRUNCATE with CASCADE
                if self.db_engine in ["postgresql", "postgres"]:
                    if tables_to_purge:
                        truncate_stmt = text(f"TRUNCATE TABLE {', '.join(tables_to_purge)} CASCADE;")
                        conn.execute(truncate_stmt)
                else:
                    # For SQLite or other engines, delete from each table
                    for table in tables_to_purge:
                        conn.execute(text(f"DELETE FROM {table};"))
                
                # Re-enable foreign key checks for SQLite
                if self.db_engine == "sqlite":
                    conn.execute(text("PRAGMA foreign_keys = ON;"))
                
            print(f"Purged data from {len(tables_to_purge)} tables")
            return self
        except Exception as e:
            print(f"Error purging database: {e}")
            raise
    
    def backup_db(self, backup_path=None):
        """
        Create a backup of the database.
        
        Args:
            backup_path (str, optional): Path to store backup. If None, uses default location.
            
        Returns:
            str: Path to the backup file
        """
        import shutil
        import subprocess
        from datetime import datetime
        
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.db_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            if self.db_engine == "sqlite":
                backup_path = os.path.join(backup_dir, f"{self.db_name}_{timestamp}.db")
                
                if os.path.exists(self.db_file):
                    shutil.copy2(self.db_file, backup_path)
                    print(f"Database backed up to {backup_path}")
                    return backup_path
                else:
                    raise FileNotFoundError(f"Database file {self.db_file} not found")
                    
            elif self.db_engine in ["postgresql", "postgres"]:
                backup_path = os.path.join(backup_dir, f"{self.db_name}_{timestamp}.sql")
                
                # Use pg_dump to create a backup
                pg_dump_cmd = [
                    "pg_dump",
                    "--host", self.postgres_host,
                    "--port", self.postgres_port,
                    "--username", self.postgres_user,
                    "--format", "c",
                    "--file", backup_path,
                    self.db_name
                ]

                # Set PGPASSWORD environment variable
                env = os.environ.copy()
                env["PGPASSWORD"] = self.postgres_password

                try:
                    process = subprocess.run(
                        pg_dump_cmd,
                        env=env,
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    print(f"Database backed up to {backup_path}")
                    return backup_path
                except subprocess.CalledProcessError as e:
                    print(f"pg_dump failed with error: {e.stderr}")
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    return None
                except FileNotFoundError as e:
                    print(f"pg_dump not found. Is PostgreSQL installed? {e}")
                    return None
        
        return None

    def restore_db(self, backup_path):
        """
        Restore database from a backup file.
        
        Args:
            backup_path (str): Path to the backup file
            
        Returns:
            bool: True if restore was successful, False otherwise
        """
        import subprocess
        import shutil
        
        if not os.path.exists(backup_path):
            print(f"Backup file {backup_path} not found")
            return False
        
        # Close any existing connections
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
        
        if self.db_engine == "sqlite":
            # For SQLite, simply copy the backup file to the database location
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
                
                # Copy the backup file to the database location
                shutil.copy2(backup_path, self.db_file)
                print(f"Database restored from {backup_path}")
                
                # Reconnect to the database
                self.setup_db(run_migrations=False)
                return True
            except Exception as e:
                print(f"Error restoring database: {e}")
                return False
                
        elif self.db_engine in ["postgresql", "postgres"]:
            # For PostgreSQL, drop the existing database and create a new one
            try:
                # Drop the existing database
                self.drop_db()
                
                # Create a new database
                self._create_postgresql_db()
                
                # Restore from backup using pg_restore
                pg_restore_cmd = [
                    "pg_restore",
                    "--host", self.postgres_host,
                    "--port", self.postgres_port,
                    "--username", self.postgres_user,
                    "--dbname", self.db_name,
                    "--no-owner",  # Ignore ownership
                    "--no-privileges",  # Ignore privileges
                    backup_path
                ]
                
                # Set PGPASSWORD environment variable
                env = os.environ.copy()
                env["PGPASSWORD"] = self.postgres_password
                
                process = subprocess.run(
                    pg_restore_cmd,
                    env=env,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                print(f"Database restored from {backup_path}")
                
                # Reconnect to the database
                self.setup_db(run_migrations=False)
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"pg_restore failed with error: {e.stderr.decode('utf-8')}")
                return False
            except FileNotFoundError:
                print("pg_restore command not found. Is PostgreSQL installed?")
                return False
            except Exception as e:
                print(f"Error restoring database: {e}")
                return False
                
        return False
    
    def check_db_health(self):
        """
        Perform a health check on the database and return status information.
        
        Returns:
            dict: Health information with connection status, version, size, etc.
        """
        health = {
            "status": "unknown",
            "engine": self.db_engine,
            "database": self.db_name,
            "version": self.db_version,
            "size": None,
            "tables": [],
            "connection": False,
            "details": {}
        }
        
        try:
            if not self.engine:
                self.engine = self._connect()
                
            # Test connection
            with self.engine.connect() as conn:
                health["connection"] = True
                
                # Get table names
                inspector = inspect(self.engine)
                health["tables"] = inspector.get_table_names()
                
                # Get database size (engine specific)
                if self.db_engine == "sqlite" and os.path.exists(self.db_file):
                    health["size"] = os.path.getsize(self.db_file)
                    
            health["status"] = "healthy"
            return health
            
        except Exception as e:
            health["status"] = "unhealthy"
            health["details"]["error"] = str(e)
            return health


# Initialize the DatabaseManager
db_manager = DatabaseManager() # Use db_manager.get_db() as a dependency in your routes