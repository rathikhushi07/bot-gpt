# Architecture Documentation

## Overview

BOT GPT Backend is a FastAPI-based conversational AI system that supports both open-ended chat and document-grounded (RAG) conversations.

## Design Principles

1. **Separation of Concerns**: Clear layer separation (API → Service → Data)
2. **Modularity**: Independent, reusable components
3. **Scalability**: Designed for horizontal scaling
4. **Testability**: Dependency injection and mocking support
5. **Cost Awareness**: Token management and context optimization

---

## Layer Architecture

### 1. API Layer (`controller/routes/`)

**Responsibility**: HTTP request handling, validation, response formatting

**Components**:
- `conversations.py`: Conversation CRUD operations
- `users.py`: User management
- `documents.py`: Document upload and management
- `operations.py`: Legacy/utility endpoints

**Key Features**:
- Pydantic request/response models
- FastAPI dependency injection
- HTTP status code management
- Error response formatting

### 2. Service Layer (`services/`)

**Responsibility**: Business logic, orchestration, external integrations

#### ConversationService
- Manages conversation lifecycle
- Orchestrates LLM and RAG services
- Handles message sequencing
- Token accounting

#### LLMService
- External LLM API integration (Groq)
- Context window management
- Token estimation
- History truncation (sliding window)
- Mock mode for development

#### RAGService
- Document chunking (with overlap)
- Keyword-based retrieval
- Context construction
- Chunk management

### 3. Data Layer (`models/domain/`)

**Responsibility**: Database schema, ORM models, relationships

**Entities**:
- `User`: User accounts
- `Conversation`: Chat sessions
- `Message`: Individual messages
- `Document`: Uploaded documents
- `DocumentChunk`: Document fragments
- `ConversationDocument`: Many-to-many relationship

**Key Features**:
- SQLAlchemy ORM
- Cascade deletes
- Relationship management
- UUID primary keys

---

## Data Flow

### Open Chat Flow

```
1. User sends message
   ↓
2. API validates request
   ↓
3. ConversationService creates/updates conversation
   ↓
4. Fetches conversation history from DB
   ↓
5. Builds message list for LLM
   ↓
6. LLMService truncates history if needed
   ↓
7. Calls external LLM API
   ↓
8. Receives response
   ↓
9. Stores assistant message in DB
   ↓
10. Returns response to user
```

### RAG Flow

```
1. User uploads document
   ↓
2. RAGService chunks document
   ↓
3. Stores chunks in DB
   ↓
4. User creates RAG conversation
   ↓
5. User sends message
   ↓
6. RAGService retrieves relevant chunks
   ↓
7. Constructs context from chunks
   ↓
8. LLMService builds prompt with context
   ↓
9. Calls LLM with grounded prompt
   ↓
10. Returns contextual response
```

---

## Context Management Strategy

### Problem
LLMs have token limits (e.g., 8K tokens for Llama models)

### Solution: Sliding Window

1. **Always Keep**: System prompts
2. **Prioritize**: Most recent messages
3. **Truncate**: Old messages when exceeding limit
4. **Estimate**: ~4 chars per token

```python
def truncate_history(messages, max_tokens):
    system_msgs = [m for m in messages if m.role == "system"]
    other_msgs = [m for m in messages if m.role != "system"]
    
    # Add messages from newest to oldest until limit
    truncated = []
    current_tokens = 0
    
    for msg in reversed(other_msgs):
        tokens = estimate_tokens(msg.content)
        if current_tokens + tokens <= max_tokens:
            truncated.insert(0, msg)
            current_tokens += tokens
    
    return system_msgs + truncated
```

### Cost Optimization

1. **Caching**: Store common prompts
2. **Summarization**: Summarize old conversations
3. **Selective History**: Only send relevant messages
4. **Token Tracking**: Monitor usage per user

---

## RAG Implementation

### Document Processing

1. **Upload**: Receive document text
2. **Split**: Divide into paragraphs
3. **Chunk**: Group into ~500 char chunks with 50 char overlap
4. **Store**: Save chunks in database

### Retrieval Strategy

**Current: Keyword-Based**
- Extract keywords from user query
- Score chunks by keyword overlap
- Return top K chunks (default: 3)

**Why not embeddings?**
- Simpler implementation
- No external dependencies
- Good enough for moderate document sizes
- Fast retrieval

**Future: Embedding-Based**
- Higher accuracy
- Semantic search
- Requires vector database (Pinecone/Chroma)

### Context Construction

```python
def retrieve_context(document_ids, query, top_k=3):
    # Get all chunks from documents
    chunks = get_chunks(document_ids)
    
    # Score and rank chunks
    scored_chunks = keyword_search(query, chunks)
    
    # Take top K
    top_chunks = scored_chunks[:top_k]
    
    # Format context
    context = "\n\n".join([
        f"[Context {i+1}]\n{chunk.content}"
        for i, chunk in enumerate(top_chunks)
    ])
    
    return context
```

---

## Error Handling

### Layered Approach

1. **Database Layer**
   - Connection errors
   - Constraint violations
   - Transaction failures

2. **Service Layer**
   - Business logic errors (ValueError)
   - LLM API failures (timeout, rate limits)
   - Invalid state errors

3. **API Layer**
   - Validation errors (422)
   - Not found errors (404)
   - Authentication errors (401/403)
   - Server errors (500)

### Error Response Format

```json
{
  "error": "Error type",
  "detail": "Detailed message",
  "status_code": 400
}
```

### Retry Strategy

**LLM API calls**:
- Retry on timeout: 3 attempts
- Exponential backoff: 1s, 2s, 4s
- Fallback: Return error message

**Database operations**:
- Transaction rollback on error
- Log error details
- Return user-friendly message

---

## Scalability Analysis

### Current Architecture (0-10K users)

**Suitable for**:
- Development
- MVP/Prototype
- Small deployments

**Limitations**:
- SQLite concurrency
- Single-instance bottleneck
- No caching

### Phase 2 (10K-100K users)

**Changes**:
```
┌─────────────┐
│ Load        │
│ Balancer    │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌──▼──┐
│App 1│ │App 2│
└──┬──┘ └──┬──┘
   │       │
   └───┬───┘
       │
   ┌───▼────┐      ┌───────┐
   │Postgres│      │ Redis │
   │ Primary│◄────►│ Cache │
   └───┬────┘      └───────┘
       │
   ┌───▼────┐
   │Postgres│
   │Replica │
   └────────┘
```

**Additions**:
- PostgreSQL with replication
- Redis for caching
- Horizontal scaling (multiple app instances)
- Load balancer (nginx/HAProxy)

### Phase 3 (100K-1M users)

**Changes**:
- Message queue (RabbitMQ/Kafka) for async LLM calls
- Object storage (S3/MinIO) for documents
- Database sharding by user_id
- CDN for static content

### Phase 4 (1M+ users)

**Architecture**:
```
┌─────────────────────────────────────────┐
│           API Gateway (Kong)            │
└────────────┬────────────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
┌───▼───┐ ┌──▼──┐ ┌──▼──┐
│Convo  │ │User │ │Doc  │
│Service│ │Svc  │ │Svc  │
└───┬───┘ └──┬──┘ └──┬──┘
    │        │       │
┌───▼────────▼───────▼────┐
│   Message Queue (Kafka) │
└────────────┬─────────────┘
             │
    ┌────────┼────────┐
┌───▼───┐ ┌──▼──┐ ┌──▼──┐
│LLM    │ │RAG  │ │DB   │
│Worker │ │Svc  │ │Shard│
└───────┘ └─────┘ └─────┘
```

**Changes**:
- Microservices architecture
- Event-driven communication
- Database sharding
- Dedicated LLM workers
- Service mesh (Istio)

---

## Security Considerations

### Current Implementation

- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ CORS configuration
- ❌ Authentication (not implemented)
- ❌ Rate limiting (not implemented)
- ❌ API key management (basic)

### Production Requirements

1. **Authentication & Authorization**
   - JWT tokens
   - User roles and permissions
   - API key management

2. **Rate Limiting**
   - Per-user limits
   - Per-IP limits
   - Token usage quotas

3. **Data Protection**
   - Encrypt sensitive data at rest
   - HTTPS/TLS in transit
   - Secure API key storage (Vault)

4. **Monitoring & Logging**
   - Structured logging
   - Security event tracking
   - Audit trails

---

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Service logic
- Utility functions
- Mocked dependencies

### Integration Tests (`tests/integration/`)
- API endpoints
- Database operations
- End-to-end flows

### Test Coverage Goals
- Target: 80%+ coverage
- Critical paths: 100% coverage

---

## Deployment Strategy

### Development
```bash
python -m uvicorn app:app --reload
```

### Staging
```bash
docker-compose up -d
```

### Production
```bash
# Container orchestration (Kubernetes)
kubectl apply -f deployment.yaml
```

---

## Monitoring & Observability

### Metrics to Track

1. **Performance**
   - Request latency (p50, p95, p99)
   - LLM API response time
   - Database query time

2. **Business**
   - Active users
   - Conversations per day
   - Messages per conversation
   - Token usage

3. **Reliability**
   - Error rate
   - API availability
   - Database connection pool

### Tools

- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **ELK Stack**: Log aggregation
- **Sentry**: Error tracking

---

## Future Enhancements

1. **Conversation Features**
   - Conversation sharing
   - Export conversations
   - Search in conversations
   - Message editing

2. **RAG Improvements**
   - Vector embeddings
   - Hybrid search (keyword + semantic)
   - Multi-modal documents (images, PDFs)
   - Document versioning

3. **LLM Features**
   - Multiple LLM providers
   - Model selection per conversation
   - Streaming responses
   - Function calling

4. **Enterprise Features**
   - Multi-tenancy
   - SSO integration
   - Audit logs
   - Admin dashboard

