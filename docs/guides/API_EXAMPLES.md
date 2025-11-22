# API Usage Examples

Complete examples for testing BOT GPT Backend API.

## Quick Start Guide

### Step 1: Create a User

```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com"
  }'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2024-11-21T10:00:00Z"
}
```

**Save the `id` value - you'll need it for other requests!**

---

## Scenario 1: Open Chat Conversation

### Create Conversation

```bash
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "first_message": "Hello! Can you help me learn about Python?",
    "mode": "open_chat"
  }'
```

Response:
```json
{
  "conversation_id": "conv-123-abc",
  "message": {
    "id": "msg-456",
    "role": "assistant",
    "content": "Hello! I'd be happy to help you learn about Python...",
    "tokens": 150,
    "sequence_number": 2,
    "created_at": "2024-11-21T10:01:00Z"
  },
  "total_tokens": 180
}
```

### Continue Conversation

```bash
curl -X POST "http://localhost:8000/api/v1/conversations/conv-123-abc/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What are the main features of Python?"
  }'
```

### Get Conversation History

```bash
curl "http://localhost:8000/api/v1/conversations/conv-123-abc"
```

Response:
```json
{
  "id": "conv-123-abc",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Hello! Can you help me learn about Python?",
  "mode": "open_chat",
  "is_active": true,
  "total_tokens": 450,
  "created_at": "2024-11-21T10:01:00Z",
  "updated_at": "2024-11-21T10:05:00Z",
  "messages": [
    {
      "id": "msg-001",
      "role": "user",
      "content": "Hello! Can you help me learn about Python?",
      "tokens": 30,
      "sequence_number": 1,
      "created_at": "2024-11-21T10:01:00Z"
    },
    {
      "id": "msg-002",
      "role": "assistant",
      "content": "Hello! I'd be happy to help...",
      "tokens": 150,
      "sequence_number": 2,
      "created_at": "2024-11-21T10:01:00Z"
    }
  ]
}
```

---

## Scenario 2: RAG (Document-Grounded) Conversation

### Step 1: Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "python_guide.txt",
    "content": "Python is a high-level, interpreted programming language. It was created by Guido van Rossum and first released in 1991. Python is known for its simple and readable syntax, which makes it an excellent choice for beginners. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python is widely used in web development, data science, artificial intelligence, scientific computing, and automation.",
    "mime_type": "text/plain"
  }'
```

Response:
```json
{
  "id": "doc-789",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "python_guide.txt",
  "file_size": 450,
  "mime_type": "text/plain",
  "chunk_count": 3,
  "created_at": "2024-11-21T10:10:00Z"
}
```

### Step 2: Create RAG Conversation

```bash
curl -X POST "http://localhost:8000/api/v1/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "first_message": "Who created Python and when?",
    "mode": "grounded_rag",
    "document_ids": ["doc-789"]
  }'
```

Response:
```json
{
  "conversation_id": "conv-rag-001",
  "message": {
    "id": "msg-rag-002",
    "role": "assistant",
    "content": "Based on the document, Python was created by Guido van Rossum and first released in 1991.",
    "tokens": 120,
    "sequence_number": 2,
    "created_at": "2024-11-21T10:11:00Z"
  },
  "total_tokens": 150
}
```

### Step 3: Continue with Context

```bash
curl -X POST "http://localhost:8000/api/v1/conversations/conv-rag-001/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What is Python used for?"
  }'
```

The assistant will answer based on the document content.

---

## Listing and Management

### List All Conversations for a User

```bash
curl "http://localhost:8000/api/v1/conversations?user_id=550e8400-e29b-41d4-a716-446655440000&page=1&page_size=20"
```

Response:
```json
{
  "items": [
    {
      "id": "conv-123-abc",
      "title": "Hello! Can you help me learn about Python?",
      "mode": "open_chat",
      "is_active": true,
      "message_count": 4,
      "total_tokens": 450,
      "created_at": "2024-11-21T10:01:00Z",
      "updated_at": "2024-11-21T10:05:00Z",
      "last_message": "Great question! Let me explain..."
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### List All Documents

```bash
curl "http://localhost:8000/api/v1/documents?user_id=550e8400-e29b-41d4-a716-446655440000"
```

### Delete Conversation

```bash
curl -X DELETE "http://localhost:8000/api/v1/conversations/conv-123-abc"
```

### Delete Document

```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/doc-789"
```

---

## Health Check

```bash
curl "http://localhost:8000/health"
```

Response:
```json
{
  "status": "UP",
  "timestamp": "2024-11-21T10:30:00Z",
  "database": "connected",
  "llm_provider": "mock"
}
```

---

## Using with Postman

1. Import this as a collection
2. Set base URL variable: `http://localhost:8000`
3. Create environment variables:
   - `user_id`
   - `conversation_id`
   - `document_id`

---

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Create user
response = requests.post(f"{BASE_URL}/users", json={
    "username": "testuser",
    "email": "test@example.com"
})
user = response.json()
user_id = user["id"]

# Create conversation
response = requests.post(f"{BASE_URL}/conversations", json={
    "user_id": user_id,
    "first_message": "Hello!",
    "mode": "open_chat"
})
conv = response.json()
conversation_id = conv["conversation_id"]

# Add message
response = requests.post(
    f"{BASE_URL}/conversations/{conversation_id}/messages",
    json={"content": "Tell me more"}
)
reply = response.json()
print(reply["message"]["content"])
```

---

## JavaScript/Node.js Client Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000/api/v1';

async function main() {
  // Create user
  const userResponse = await axios.post(`${BASE_URL}/users`, {
    username: 'testuser',
    email: 'test@example.com'
  });
  const userId = userResponse.data.id;

  // Create conversation
  const convResponse = await axios.post(`${BASE_URL}/conversations`, {
    user_id: userId,
    first_message: 'Hello!',
    mode: 'open_chat'
  });
  const conversationId = convResponse.data.conversation_id;

  // Add message
  const msgResponse = await axios.post(
    `${BASE_URL}/conversations/${conversationId}/messages`,
    { content: 'Tell me more' }
  );
  console.log(msgResponse.data.message.content);
}

main();
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Validation error",
  "detail": "username already exists"
}
```

### 404 Not Found
```json
{
  "detail": "Conversation not found: conv-123"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "first_message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "Failed to process request"
}
```

