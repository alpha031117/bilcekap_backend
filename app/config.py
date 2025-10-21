import os
from typing import Optional


class Settings:
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./bilcekap.db")
    
    # API settings
    API_V1_STR: str = "/api/v1.0"
    PROJECT_NAME: str = "Bilcekap Backend API"
    
    # LHDN API settings
    LHDN_API_URL: str = os.getenv("LHDN_API_URL", "https://api.ldhn.gov.my")
    LHDN_API_KEY: Optional[str] = os.getenv("LHDN_API_KEY")
    LHDN_API_TIMEOUT: int = int(os.getenv("LHDN_API_TIMEOUT", "30"))
    
    # Security settings (for future use)
    SECRET_KEY: Optional[str] = os.getenv("SECRET_KEY")
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Vite default
    ]


settings = Settings()
