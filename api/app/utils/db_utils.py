import os, json
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base

class DatabaseManager:
    project_root = os.path.join(os.path.dirname(os.path.dirname(__file__)))

    def __init__(self):
        # Load the .env file from the project root
        load_dotenv(dotenv_path=os.path.join(project_root, ".env"))

        self.db_engine = os.getenv("DB_ENGINE", "sqlite")
        self.mode = os.getenv("ENV_MODE", "development")
        self.db_name = self._set_db_name()
        self.db_suffix = self._build_db_suffix()
        self.db_url = self._build_db_url()

        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _get_package_name(self, project_root):
        """Get the project name from the package.json file"""
        try:
            with open(os.path.join(project_root, "package.json"), "r") as f:
                package_json = json.load(f)
                return package_json["name"]

        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None
    def _set_db_name(self):
        if (os.getenv("DB_NAME")):
            return os.getenv("DB_NAME")
        # If no DB_NAME is set, check the package.json file for the project name
        elif (self._get_package_name()):
            return self._get_package_name()
        else:
            return "app"
    
    def _build_db_suffix(self):
        if self.mode == "test":
            # Get the latest alembic migration version from the migrations folder
            migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations")
            versions = [d for d in os.listdir(migrations_dir) if os.path.isdir(os.path.join(migrations_dir, d))]
            latest_version = max(versions)
            return f"_{latest_version}"
        else:
            return None

    def _build_db_url(self):
        if self.db_engine == "sqlite":
            db_dir = os.getenv("DB_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"))
            db_name = os.getenv("DB_NAME", "test")

            if self.mode == "test" and self.db_suffix:
                db_name = f"{db_name}{self.db_suffix}"

            db_data_path = os.path.join(db_dir, f"{db_name}.db")
            return f"sqlite:///{db_data_path}"
        else:
            db_user = os.getenv("DB_USER")
            db_password = os.getenv("DB_PASSWORD")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME")

            if self.mode == "test" and self.db_suffix:
                db_name = f"{db_name}{self.db_suffix}"

            return f"{self.db_engine}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    def get_db(self):
        db: Session = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def _get_db_url(self):
        return self.db_url

    def create_tables(self):
        Base.metadata.create_all(self.engine)
    
    def setup_test_db(self):
        

# Initialize the DatabaseManager
db_manager = DatabaseManager() # Use db_manager.get_db() as a dependency in your routes