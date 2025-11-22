from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging
import os

from ..models.domain.entities import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            db_path = os.getenv("DATABASE_PATH", "./data/botgpt.db")
            os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        
        if database_url.startswith("sqlite"):
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=False
            )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database initialized: {database_url}")
    
    def create_tables(self):
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise
    
    def drop_tables(self):
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")
    
    @contextmanager
    def get_session(self) -> Session:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


db_manager: DatabaseManager = None


def init_database(database_url: str = None) -> DatabaseManager:
    global db_manager
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    return db_manager


def get_db_manager() -> DatabaseManager:
    if db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return db_manager
