import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "QuickBite Online Food Ordering Application"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api"
    
    # Cryptographic Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "quickbite_super_secret_jwt_signing_key_for_development_only_256bit")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./quickbite.db")
    
    # Rate Limiting
    MAX_LOGIN_ATTEMPTS_PER_MIN: int = 5
    
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
