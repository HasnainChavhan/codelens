import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    db_host = os.getenv("POSTGRES_HOST")
    if db_host:
        db_user = os.getenv("POSTGRES_USER", "admin")
        db_pass = os.getenv("POSTGRES_PASSWORD", "password")
        db_name = os.getenv("POSTGRES_DB", "ecommerce")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    else:
        # Default to SQLite for simplicity if postgres isn't configured
        os.makedirs("data", exist_ok=True)
        db_url = "sqlite:///data/ecommerce.db"
    
    return create_engine(db_url)
