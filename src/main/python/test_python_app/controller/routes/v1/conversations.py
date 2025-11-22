from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ....core.database import get_db_manager
from ....models.schemas.request_schemas import (
    CreateConversationRequest,
    AddMessageRequest,
    ConversationResponse,
    ConversationDetail,
    PaginatedResponse,
    ErrorResponse
)
from ....services.conversation_service import ConversationService
from ....services.llm_service import LLMService
from ....services.rag_service import RAGService

router = APIRouter(prefix="/conversations", tags=["Conversations"])

# Service instances (will be initialized in app startup)
conversation_service: Optional[ConversationService] = None


def get_conversation_service() -> ConversationService:
    if conversation_service is None:
        raise HTTPException(status_code=500, detail="Conversation service not initialized")
    return conversation_service


def init_conversation_service(llm_service: LLMService, rag_service: RAGService):
    global conversation_service
    conversation_service = ConversationService(llm_service, rag_service)


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=201,
    summary="Create new conversation",
    description="Start a new conversation with the first message"
)
async def create_conversation(
    request: CreateConversationRequest,
    service: ConversationService = Depends(get_conversation_service)
):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            result = await service.create_conversation(db, request)
            return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List conversations",
    description="Get paginated list of conversations for a user"
)
def list_conversations(
    user_id: str = Query(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ConversationService = Depends(get_conversation_service)
):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            result = service.get_conversations(db, user_id, page, page_size)
            return PaginatedResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get conversation details",
    description="Get full conversation with message history"
)
def get_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service)
):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            return service.get_conversation_detail(db, conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.post(
    "/{conversation_id}/messages",
    response_model=ConversationResponse,
    summary="Add message to conversation",
    description="Add a user message and get AI assistant response"
)
async def add_message(
    conversation_id: str,
    request: AddMessageRequest,
    service: ConversationService = Depends(get_conversation_service)
):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            result = await service.add_message(db, conversation_id, request)
            return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.delete(
    "/{conversation_id}",
    status_code=204,
    summary="Delete conversation",
    description="Delete a conversation and all its messages"
)
def delete_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service)
):
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_session() as db:
            service.delete_conversation(db, conversation_id)
            return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

