import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load the .env file from the project root
load_dotenv()

# Retrieve environment variables
DATABASE_PROVIDER = os.getenv("DATABASE_PROVIDER")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_DIR = os.getenv("DATABASE_DIR", "data")  # Default to "data" if not set

# Check if required variables are set
if not DATABASE_PROVIDER:
    raise ValueError("DATABASE_PROVIDER not found in .env file")
if not DATABASE_NAME:
    raise ValueError("DATABASE_NAME not found in .env file")

# Ensure the provider is SQLite
if DATABASE_PROVIDER.lower() != "sqlite":
    raise ValueError("This script only supports SQLite databases")

# Construct the database file path
db_file = f"{DATABASE_NAME}.db"
db_path = os.path.join(DATABASE_DIR, db_file) if DATABASE_DIR else db_file

# Ensure the directory exists (if specified)
if DATABASE_DIR:
    os.makedirs(DATABASE_DIR, exist_ok=True)

# Construct the SQLite database URL
DATABASE_URL = f"sqlite:///{db_path}"

# Create the database file by connecting to it
engine = create_engine(DATABASE_URL)
with engine.connect() as connection:
    pass  # Connection creates the file if it doesn't exist

print(f"Database file created at {db_path}")