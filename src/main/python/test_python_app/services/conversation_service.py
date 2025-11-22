import logging
from typing import Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from .llm_service import LLMService
from .rag_service import RAGService
from ..models.domain.entities import (
    User, Conversation, Message, Document,
    ConversationMode, MessageRole, ConversationDocument
)
from ..models.schemas.request_schemas import (
    CreateConversationRequest, AddMessageRequest,
    ConversationSummary, ConversationDetail, MessageResponse,
    ConversationResponse
)

logger = logging.getLogger(__name__)


class ConversationService:
    
    def __init__(self, llm_service: LLMService, rag_service: RAGService):
        self.llm_service = llm_service
        self.rag_service = rag_service
        logger.info("Conversation Service initialized")
    
    async def create_conversation(
        self,
        db: Session,
        request: CreateConversationRequest
    ) -> ConversationResponse:
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise ValueError(f"User not found: {request.user_id}")
        
        if request.mode == "grounded_rag" and request.document_ids:
            doc_count = db.query(Document).filter(
                Document.id.in_(request.document_ids),
                Document.user_id == request.user_id
            ).count()
            if doc_count != len(request.document_ids):
                raise ValueError("One or more documents not found or don't belong to user")
        
        conversation = Conversation(
            user_id=request.user_id,
            title=request.title or self._generate_title(request.first_message),
            mode=ConversationMode(request.mode.value),
            is_active=True,
            total_tokens=0
        )
        db.add(conversation)
        db.flush()
        
        if request.mode == "grounded_rag" and request.document_ids:
            for doc_id in request.document_ids:
                conv_doc = ConversationDocument(
                    conversation_id=conversation.id,
                    document_id=doc_id
                )
                db.add(conv_doc)
        
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=request.first_message,
            tokens=self.llm_service.estimate_tokens(request.first_message),
            sequence_number=1
        )
        db.add(user_message)
        db.flush()
        
        assistant_message = await self._generate_assistant_response(
            db=db,
            conversation=conversation,
            user_message_content=request.first_message,
            sequence_number=2
        )
        
        conversation.total_tokens = user_message.tokens + assistant_message.tokens
        db.commit()
        
        logger.info(f"Created conversation {conversation.id} with mode {conversation.mode}")
        
        return ConversationResponse(
            conversation_id=conversation.id,
            message=MessageResponse.model_validate(assistant_message),
            total_tokens=conversation.total_tokens
        )
    
    async def add_message(
        self,
        db: Session,
        conversation_id: str,
        request: AddMessageRequest
    ) -> ConversationResponse:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        if not conversation.is_active:
            raise ValueError("Conversation is inactive")
        
        max_seq = db.query(func.max(Message.sequence_number)).filter(
            Message.conversation_id == conversation_id
        ).scalar() or 0
        
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=request.content,
            tokens=self.llm_service.estimate_tokens(request.content),
            sequence_number=max_seq + 1
        )
        db.add(user_message)
        db.flush()
        
        assistant_message = await self._generate_assistant_response(
            db=db,
            conversation=conversation,
            user_message_content=request.content,
            sequence_number=max_seq + 2
        )
        
        conversation.total_tokens += user_message.tokens + assistant_message.tokens
        db.commit()
        
        logger.info(f"Added message to conversation {conversation_id}")
        
        return ConversationResponse(
            conversation_id=conversation.id,
            message=MessageResponse.model_validate(assistant_message),
            total_tokens=conversation.total_tokens
        )
    
    async def _generate_assistant_response(
        self,
        db: Session,
        conversation: Conversation,
        user_message_content: str,
        sequence_number: int
    ) -> Message:
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.sequence_number).all()
        
        context = None
        if conversation.mode == ConversationMode.GROUNDED_RAG:
            document_ids = [doc.id for doc in conversation.documents]
            if document_ids:
                context = self.rag_service.retrieve_context(
                    db=db,
                    document_ids=document_ids,
                    query=user_message_content,
                    top_k=3
                )
        
        llm_messages = []
        
        system_prompt = self.llm_service.create_system_prompt(
            mode=conversation.mode.value,
            context=context
        )
        llm_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            llm_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
        
        if not messages or messages[-1].role != MessageRole.USER:
            llm_messages.append({"role": "user", "content": user_message_content})
        
        try:
            response = await self.llm_service.generate_response(
                messages=llm_messages,
                temperature=0.7,
                max_response_tokens=1000
            )
            
            content = response["content"]
            tokens = response["tokens_used"]
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            content = "I apologize, but I'm having trouble generating a response right now. Please try again."
            tokens = self.llm_service.estimate_tokens(content)
        
        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=content,
            tokens=tokens,
            sequence_number=sequence_number
        )
        db.add(assistant_message)
        
        return assistant_message
    
    def get_conversations(
        self,
        db: Session,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict:
        total = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).count()
        
        offset = (page - 1) * page_size
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).offset(offset).limit(page_size).all()
        
        summaries = []
        for conv in conversations:
            message_count = len(conv.messages)
            last_message = conv.messages[-1].content if conv.messages else None
            
            summary = ConversationSummary(
                id=conv.id,
                title=conv.title,
                mode=conv.mode,
                is_active=conv.is_active,
                message_count=message_count,
                total_tokens=conv.total_tokens,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                last_message=last_message[:100] if last_message else None
            )
            summaries.append(summary)
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": summaries,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    def get_conversation_detail(self, db: Session, conversation_id: str) -> ConversationDetail:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        messages = [MessageResponse.model_validate(msg) for msg in conversation.messages]
        document_ids = [doc.id for doc in conversation.documents] if conversation.documents else None
        
        return ConversationDetail(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            mode=conversation.mode,
            is_active=conversation.is_active,
            total_tokens=conversation.total_tokens,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=messages,
            document_ids=document_ids
        )
    
    def delete_conversation(self, db: Session, conversation_id: str) -> bool:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if not conversation:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        db.delete(conversation)
        db.commit()
        
        logger.info(f"Deleted conversation {conversation_id}")
        return True
    
    def _generate_title(self, first_message: str, max_length: int = 50) -> str:
        title = first_message[:max_length]
        if len(first_message) > max_length:
            title += "..."
        return title
