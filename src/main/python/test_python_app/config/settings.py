"""
Application settings
"""
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """Application metadata"""
    name: str = "test-python-app"
    version: str = "1.0.0"


class ServerConfig(BaseModel):
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"


class Settings(BaseSettings):
    """Application settings"""
    
    app: AppConfig = AppConfig()
    server: ServerConfig = ServerConfig()
    logging: LoggingConfig = LoggingConfig()
    
    class Config:
        env_file = ".env"
        case_sensitive = False
