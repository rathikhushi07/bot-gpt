from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import yaml
import os
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

from .controller.routes.v1 import operations, conversations, users, documents
from .config.settings import Settings
from .core.database import init_database, get_db_manager
from .services.llm_service import LLMService
from .services.rag_service import RAGService
from .models.schemas.request_schemas import HealthCheckResponse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings: Settings = None


def load_settings() -> Settings:
    profile = os.getenv("PROFILE", "local")
    project_root = Path(__file__).parent.parent.parent.parent.parent
    app_name = "test-python-app"
    config_file = project_root / f"{app_name}-{profile}.yaml"
    
    config_data = {}
    
    if config_file.exists():
        logger.info(f"Loading configuration from: {config_file}")
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load YAML config: {e}, using environment variables")
    else:
        logger.info("No YAML config found, using environment variables and defaults")
    
    if os.getenv("SERVER_PORT") or os.getenv("PORT"):
        port = int(os.getenv("SERVER_PORT") or os.getenv("PORT"))
        if 'server' not in config_data:
            config_data['server'] = {}
        config_data['server']['port'] = port
    
    try:
        return Settings(**config_data)
    except Exception as e:
        logger.warning(f"Error loading settings: {e}, using defaults")
        return Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global settings
    
    logger.info("Starting BOT GPT Backend...")
    
    try:
        settings = load_settings()
        logger.info(f"Port: {settings.server.port}")
        
        database_url = os.getenv("DATABASE_URL")
        init_database(database_url)
        logger.info("Database initialized")
        
        llm_provider = os.getenv("LLM_PROVIDER", "mock")
        llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")
        llm_service = LLMService(provider=llm_provider, api_key=llm_api_key)
        
        rag_service = RAGService(chunk_size=500, chunk_overlap=50)
        
        from .controller.routes.v1.conversations import init_conversation_service
        from .controller.routes.v1.documents import init_rag_service
        init_conversation_service(llm_service, rag_service)
        init_rag_service(rag_service)
        
        logger.info("BOT GPT Backend started successfully")
    except Exception as err:
        logger.error(f"Failed to initialize application: {str(err)}")
        raise
    
    yield
    
    logger.info("Shutting down BOT GPT Backend...")


app = FastAPI(
    title="BOT GPT Backend",
    description="Conversational AI Backend with LLM Integration and RAG Support",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversations.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(operations.router)


@app.get("/")
async def root():
    return {
        "name": "BOT GPT Backend",
        "version": "1.0.0",
        "status": "running",
        "description": "Conversational AI Backend with LLM Integration",
        "docs": "/api/docs"
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    try:
        db_manager = get_db_manager()
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    llm_provider = os.getenv("LLM_PROVIDER", "mock")
    
    return HealthCheckResponse(
        status="UP",
        timestamp=datetime.now(),
        database=db_status,
        llm_provider=llm_provider
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
