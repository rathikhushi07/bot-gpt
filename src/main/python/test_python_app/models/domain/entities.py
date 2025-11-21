"""
Domain entities
Equivalent to @Entity classes in Spring Boot
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ExampleEntity(Base):
    """Example entity"""
    __tablename__ = "example"
    
    id = Column(Integer, primary_key=True)
    # TODO: Define entity fields



