import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load the .env file from the project root
load_dotenv()

# Retrieve environment variables
DB_ENGINE = os.getenv("DB_ENGINE")
DB_NAME = os.getenv("DB_NAME")
DB_DIR = os.getenv("DB_DIR", "data")  # Default to "data" if not set

# Check if required variables are set
if not DB_ENGINE:
    raise ValueError("DB_ENGINE not found in .env file")
if not DB_NAME:
    raise ValueError("DB_NAME not found in .env file")

# Ensure the provider is SQLite
if DB_ENGINE.lower() != "sqlite":
    raise ValueError("This script only supports SQLite databases")

# Construct the database file path
db_file = f"{DB_NAME}.db"
db_path = os.path.join(DB_DIR, db_file) if DB_DIR else db_file

# Ensure the directory exists (if specified)
if DB_DIR:
    os.makedirs(DB_DIR, exist_ok=True)

# Construct the SQLite database URL
DB_URL = f"sqlite:///{db_path}"

# Create the database file by connecting to it
engine = create_engine(DB_URL)
with engine.connect() as connection:
    pass  # Connection creates the file if it doesn't exist

print(f"Database file created at {db_path}")