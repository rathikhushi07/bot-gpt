"""
Application entry point
"""
from fastapi import FastAPI
import logging
import yaml
import os
from pathlib import Path
from contextlib import asynccontextmanager

# Import routers
from .controller.routes.v1 import operations

# Import configurations
from .config.settings import Settings

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global settings
settings: Settings = None


def load_settings() -> Settings:
    """Load settings from YAML file"""
    profile = os.getenv("PROFILE", "local")
    project_root = Path(__file__).parent.parent.parent.parent.parent
    app_name = "test-python-app"
    config_file = project_root / f"{app_name}-{profile}.yaml"
    
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_file}, using defaults")
        return Settings()
    
    logger.info(f"Loading configuration from: {config_file}")
    
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f) or {}
    
    # Override port from environment if set
    if os.getenv("SERVER_PORT"):
        if 'server' not in config_data:
            config_data['server'] = {}
        config_data['server']['port'] = int(os.getenv("SERVER_PORT"))
    
    return Settings(**config_data)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global settings
    
    # Startup
    logger.info("Starting application...")
    
    try:
        settings = load_settings()
        logger.info(f"Port: {settings.server.port}")
        logger.info("Application started successfully")
    except Exception as err:
        logger.error(f"Failed to initialize application: {str(err)}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="test-python-app",
    description="Test Python Application",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(operations.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "test-python-app API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "UP"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
