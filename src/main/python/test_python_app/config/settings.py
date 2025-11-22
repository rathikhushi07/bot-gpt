from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional


class AppConfig(BaseModel):
    name: str = "test-python-app"
    version: str = "1.0.0"


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class LoggingConfig(BaseModel):
    level: str = "INFO"


class Settings(BaseSettings):
    
    app: AppConfig = AppConfig()
    server: ServerConfig = ServerConfig()
    logging: LoggingConfig = LoggingConfig()
    
    port: Optional[int] = None
    database_path: Optional[str] = None
    database_url: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    log_level: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"
