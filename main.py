from sqlalchemy import create_engine
# from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

# Load environment variables from .env (if present)
load_dotenv()

# Prefer an explicit DATABASE_URL (already used by this project), otherwise fall back
# to the individual variables shown in Supabase's basic connection example.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")

    missing = [k for k, v in [("user", USER), ("password", PASSWORD), ("host", HOST), ("port", PORT), ("dbname", DBNAME)] if not v]
    if missing:
        raise ValueError(
            "Missing database configuration. Set DATABASE_URL or: "
            + ", ".join(missing)
            + " in your .env"
        )

    # Construct the SQLAlchemy connection string
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# If using Supabase Transaction Pooler or Session Pooler, disable SQLAlchemy client-side pooling:
# https://docs.sqlalchemy.org/en/20/core/pooling.html#switching-pool-implementations
# engine = create_engine(DATABASE_URL, poolclass=NullPool)

# Test the connection
try:
    with engine.connect() as connection:
        connection.exec_driver_sql("select 1")
        print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")

