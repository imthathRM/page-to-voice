import os
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, urlparse
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Locate and load the .env file
env_path = Path(__file__).resolve().parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / ".env"

load_dotenv(dotenv_path=env_path)

database_url = os.getenv("DATABASE_URL") or os.getenv("SERVICE_URI")
connect_args = {}

if database_url:
    parsed = urlparse(database_url)
    query = parse_qs(parsed.query)

    # Detect SSL requirement from query string or DB_SSL_MODE
    ssl_mode = (
        query.get("ssl-mode", [""])[0]
        or query.get("ssl_mode", [""])[0]
        or os.getenv("DB_SSL_MODE", "")
    )
    if ssl_mode.upper() in ("REQUIRED", "VERIFY_CA", "VERIFY_IDENTITY", "TRUE", "1"):
        connect_args["ssl"] = {"ssl_mode": "REQUIRED"}

    password = quote_plus(parsed.password) if parsed.password else ""
    port_part = f":{parsed.port}" if parsed.port else ""
    user_part = f"{parsed.username}:{password}@" if parsed.username else ""
    db_name = parsed.path.lstrip("/") or "defaultdb"

    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{user_part}{parsed.hostname}{port_part}/{db_name}"
else:
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "page_to_voice_db")
    db_ssl_mode = os.getenv("DB_SSL_MODE", "")

    if db_ssl_mode.upper() in ("REQUIRED", "VERIFY_CA", "VERIFY_IDENTITY", "TRUE", "1"):
        connect_args["ssl"] = {"ssl_mode": "REQUIRED"}

    encoded_password = quote_plus(db_password)
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
    )

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and ensures closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
