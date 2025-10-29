import os
from typing import Optional
from pathlib import Path

# Load environment variables from .env if available
try:
    from dotenv import load_dotenv
    # Try CWD .env first (when running from project root)
    load_dotenv(dotenv_path=Path(".env"), override=False)
    # Also try project-root .env relative to this file, in case CWD differs
    project_root_env = Path(__file__).resolve().parents[2] / ".env"
    if project_root_env.exists():
        load_dotenv(dotenv_path=project_root_env, override=False)
except Exception:
    # dotenv is optional; continue if not installed
    pass


class Settings:
    # Database settings (defaults to MySQL on localhost:3306, db=bilcekap)
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "bilcekap")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )
    
    # API settings
    API_V1_STR: str = "/api/v1.0"
    PROJECT_NAME: str = "Bilcekap Backend API"
    
    # LHDN API settings
    LHDN_API_URL: str = os.getenv("LHDN_API_URL")
    LHDN_API_KEY: Optional[str] = os.getenv("LHDN_API_KEY")
    LHDN_API_TIMEOUT: int = int(os.getenv("LHDN_API_TIMEOUT", "30"))
    
    # MyInvois OAuth settings
    MYINVOIS_TOKEN_URL: str = os.getenv(
        "MYINVOIS_TOKEN_URL", "https://api.myinvois.hasil.gov.my/connect/token"
    )
    MYINVOIS_API_BASE: str = os.getenv(
        "MYINVOIS_API_BASE", "https://api.myinvois.hasil.gov.my/api/v1.0"
    )
    MYINVOIS_CLIENT_ID: Optional[str] = os.getenv("MYINVOIS_CLIENT_ID")
    MYINVOIS_CLIENT_SECRET: Optional[str] = os.getenv("MYINVOIS_CLIENT_SECRET")
    MYINVOIS_SCOPE: str = os.getenv("MYINVOIS_SCOPE", "InvoicingAPI")
    MYINVOIS_GRANT_TYPE: str = os.getenv("MYINVOIS_GRANT_TYPE", "client_credentials")
    
    # Security settings (for future use)
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Vite default
    ]


settings = Settings()
