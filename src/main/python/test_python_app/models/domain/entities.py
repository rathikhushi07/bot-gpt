import enum
import uuid

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum, Boolean, Float
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class ConversationMode(str, enum.Enum):
    OPEN_CHAT = "open_chat"
    GROUNDED_RAG = "grounded_rag"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    mode = Column(Enum(ConversationMode), nullable=False, default=ConversationMode.OPEN_CHAT)
    is_active = Column(Boolean, default=True, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    documents = relationship("Document", secondary="conversation_documents", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, mode={self.mode}, title={self.title})>"


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    tokens = Column(Integer, default=0, nullable=False)
    sequence_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, seq={self.sequence_number})>"


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    conversations = relationship("Conversation", secondary="conversation_documents", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"


class ConversationDocument(Base):
    __tablename__ = "conversation_documents"
    
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
