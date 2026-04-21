import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    github_token: str
    semantic_scholar_api_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite:///./meta_ml.db"
    
    # Model Paths
    model_path: str = "models/meta_ml_v1.joblib"
    
    # NLP Configuration
    transformer_model: str = "all-MiniLM-L6-v2"
    spacy_model: str = "en_core_web_sm"
    
    # Training Configuration
    test_size: float = 0.2
    random_state: int = 42
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Initialize settings
settings = Settings()
