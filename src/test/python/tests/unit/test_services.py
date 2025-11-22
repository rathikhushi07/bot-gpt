import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from test_python_app.services.llm_service import LLMService
from test_python_app.services.rag_service import RAGService
from test_python_app.services.conversation_service import ConversationService
from test_python_app.models.domain.entities import User, Conversation, Message, Document, DocumentChunk, ConversationMode, MessageRole
from test_python_app.models.schemas.request_schemas import CreateConversationRequest, AddMessageRequest


class TestLLMService:
    
    def test_estimate_tokens(self):
        llm_service = LLMService(provider="mock")
        text = "Hello world"
        tokens = llm_service.estimate_tokens(text)
        assert tokens > 0
        assert tokens == len(text) // 4
    
    def test_truncate_history_basic(self):
        llm_service = LLMService(provider="mock")
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        truncated = llm_service.truncate_history(messages, max_context_tokens=1000)
        assert len(truncated) <= len(messages)
        assert truncated[-1]["content"] == "How are you?"
    
    def test_truncate_history_keeps_system(self):
        llm_service = LLMService(provider="mock")
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        truncated = llm_service.truncate_history(messages, max_context_tokens=100)
        assert truncated[0]["role"] == "system"
    
    def test_generate_mock_response(self):
        llm_service = LLMService(provider="mock")
        messages = [{"role": "user", "content": "Hello"}]
        
        response = llm_service._generate_mock_response(messages)
        assert "content" in response
        assert "tokens_used" in response
        assert "model" in response
        assert len(response["content"]) > 0
    
    def test_create_system_prompt_open_chat(self):
        llm_service = LLMService(provider="mock")
        prompt = llm_service.create_system_prompt("open_chat")
        assert "BOT GPT" in prompt
        assert len(prompt) > 0
    
    def test_create_system_prompt_rag(self):
        llm_service = LLMService(provider="mock")
        context = "This is some context from documents."
        prompt = llm_service.create_system_prompt("grounded_rag", context=context)
        assert "BOT GPT" in prompt
        assert context in prompt


class TestRAGService:
    
    def test_chunk_document_basic(self):
        rag_service = RAGService(chunk_size=100, chunk_overlap=20)
        content = "This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three."
        
        chunks = rag_service.chunk_document(content)
        assert len(chunks) > 0
        assert all("content" in chunk for chunk in chunks)
        assert all("chunk_index" in chunk for chunk in chunks)
    
    def test_chunk_document_empty(self):
        rag_service = RAGService()
        content = ""
        
        chunks = rag_service.chunk_document(content)
        assert len(chunks) == 0
    
    def test_chunk_document_long(self):
        rag_service = RAGService(chunk_size=200, chunk_overlap=50)
        content = "\n\n".join([f"Paragraph {i} with some content." for i in range(20)])
        
        chunks = rag_service.chunk_document(content)
        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i
    
    def test_keyword_search_basic(self):
        rag_service = RAGService()
        
        chunks = [
            Mock(content="Python is a programming language"),
            Mock(content="JavaScript is also a programming language"),
            Mock(content="The weather is nice today")
        ]
        
        results = rag_service.keyword_search("programming language", chunks, top_k=2)
        assert len(results) <= 2
    
    def test_keyword_search_no_match(self):
        rag_service = RAGService()
        chunks = [Mock(content="Some random text")]
        
        results = rag_service.keyword_search("nonexistent keyword xyz", chunks, top_k=3)
        assert len(results) == 0


class TestConversationService:
    
    def test_generate_title(self):
        llm_service = LLMService(provider="mock")
        rag_service = RAGService()
        service = ConversationService(llm_service, rag_service)
        
        title = service._generate_title("Hello world")
        assert title == "Hello world"
        
        long_message = "A" * 100
        title = service._generate_title(long_message, max_length=50)
        assert len(title) <= 53
        assert title.endswith("...")
    
    @pytest.mark.asyncio
    async def test_create_conversation_basic(self):
        llm_service = LLMService(provider="mock")
        rag_service = RAGService()
        service = ConversationService(llm_service, rag_service)
        
        db = Mock(spec=Session)
        
        mock_user = Mock(spec=User)
        mock_user.id = "user-123"
        db.query.return_value.filter.return_value.first.return_value = mock_user
        
        request = CreateConversationRequest(
            user_id="user-123",
            first_message="Hello, how are you?",
            mode="open_chat"
        )
        
        db.add = Mock()
        db.flush = Mock()
        db.commit = Mock()
        
        with pytest.raises(Exception):
            await service.create_conversation(db, request)


class TestEndToEndWorkflow:
    
    @pytest.mark.asyncio
    async def test_mock_llm_conversation_flow(self):
        llm_service = LLMService(provider="mock")
        
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        response = await llm_service.generate_response(messages)
        
        assert "content" in response
        assert len(response["content"]) > 0
        assert response["tokens_used"] > 0
        assert response["model"] == "mock-model"
    
    def test_rag_document_processing_flow(self):
        rag_service = RAGService(chunk_size=500)
        
        document_content = "Python is a high-level programming language. It is widely used for web development, data science, and automation. Python has a simple and readable syntax."
        
        chunks = rag_service.chunk_document(document_content)
        assert len(chunks) > 0
        
        mock_chunks = [Mock(content=chunk["content"]) for chunk in chunks]
        results = rag_service.keyword_search("Python programming", mock_chunks, top_k=2)
        
        assert len(results) <= 2
