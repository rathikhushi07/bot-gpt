from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ConversationModeEnum(str, Enum):
    OPEN_CHAT = "open_chat"
    GROUNDED_RAG = "grounded_rag"


class MessageRoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Request Schemas
class CreateConversationRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    first_message: str = Field(..., min_length=1, max_length=10000, description="First message content")
    mode: ConversationModeEnum = Field(default=ConversationModeEnum.OPEN_CHAT, description="Conversation mode")
    document_ids: Optional[List[str]] = Field(default=None, description="Document IDs for RAG mode")
    title: Optional[str] = Field(default=None, max_length=500, description="Conversation title")


class AddMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=255, description="Username")
    email: Optional[str] = Field(default=None, max_length=255, description="Email address")


class UploadDocumentRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    filename: str = Field(..., min_length=1, max_length=500, description="Filename")
    content: str = Field(..., min_length=1, description="Document content")
    mime_type: Optional[str] = Field(default="text/plain", max_length=100, description="MIME type")


# Response Schemas
class MessageResponse(BaseModel):
    id: str
    role: MessageRoleEnum
    content: str
    tokens: int
    sequence_number: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    id: str
    title: Optional[str]
    mode: ConversationModeEnum
    is_active: bool
    message_count: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    mode: ConversationModeEnum
    is_active: bool
    total_tokens: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]
    document_ids: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    conversation_id: str
    message: MessageResponse
    total_tokens: int


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    file_size: int
    mime_type: Optional[str]
    chunk_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    items: List[ConversationSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int


class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    database: str
    llm_provider: str
