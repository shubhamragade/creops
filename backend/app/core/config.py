from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "CareOps MVP"
    DATABASE_URL: str
    RESEND_API_KEY: Optional[str] = None
    EMAIL_API_KEY: Optional[str] = None # Deprecated? Or alias?
    EMAIL_FROM: Optional[str] = None
    
    # SMTP Configuration - REMOVED per user request
    # Use Gmail Integration instead

    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:3000"

    CRON_SECRET: str = "careops-cron-key-2026"  # Shared secret for cron endpoint auth
    JWT_SECRET: str = "secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_ignore_empty=True,
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)

settings = Settings()
