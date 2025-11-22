# BOT GPT Backend

> **Conversational AI Backend with LLM Integration and RAG Support**

A production-grade FastAPI backend for conversational AI applications, supporting both open chat and document-grounded (RAG) conversations with external LLM integration.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)

---

## ✨ Features

- **🤖 Dual Conversation Modes**
  - Open Chat: General-purpose conversations with LLM
  - Grounded/RAG: Document-based conversations with context retrieval

- **📝 Complete REST API** - Full CRUD operations for users, conversations, and documents
- **🔌 LLM Integration** - Groq API (Llama 3.1) with mock mode for testing
- **📚 RAG Implementation** - Document chunking and keyword-based retrieval
- **💾 Data Persistence** - SQLAlchemy with SQLite/PostgreSQL support
- **🧪 Comprehensive Testing** - 35+ unit and integration tests

---

## 🚀 Quick Start

### One Command Start (Recommended)

```bash
python3 local_start.py
```

This automatically:
- Creates virtual environment
- Installs dependencies
- Sets up database
- Starts the server on http://localhost:8000

### Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn test_python_app.app:app --reload
```

---

## 📡 API Documentation

Once started, access:
- **Interactive API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/health

### Core Endpoints

**Users**
- `POST /api/users` - Create user
- `GET /api/users` - List users
- `GET /api/users/{id}` - Get user

**Conversations**
- `POST /api/conversations` - Create conversation
- `GET /api/conversations` - List with pagination
- `GET /api/conversations/{id}` - Get details
- `POST /api/conversations/{id}/messages` - Add message
- `DELETE /api/conversations/{id}` - Delete

**Documents (RAG)**
- `POST /api/documents` - Upload document
- `GET /api/documents` - List documents
- `DELETE /api/documents/{id}` - Delete

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌────────────────────────────────────┐ │
│  │      API Controllers               │ │
│  │  Conversations • Users • Documents │ │
│  └───────────────┬────────────────────┘ │
│                  │                       │
│  ┌───────────────▼────────────────────┐ │
│  │         Service Layer              │ │
│  │  ConversationService               │ │
│  │  • LLMService (Groq/Mock)         │ │
│  │  • RAGService (Chunking/Retrieval)│ │
│  └───────────────┬────────────────────┘ │
│                  │                       │
│  ┌───────────────▼────────────────────┐ │
│  │    Data Layer (SQLAlchemy ORM)    │ │
│  │  Users • Conversations • Messages  │ │
│  │  Documents • DocumentChunks        │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
         │                    │
         ▼                    ▼
    Database          External LLM API
   (SQLite/PG)         (Groq/Mock)
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (optional - works with defaults):

```bash
# Server (optional - defaults to 8000)
PORT=8000

# Database (optional - defaults to SQLite)
DATABASE_PATH=./data/botgpt.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/botgpt

# LLM Provider (optional - defaults to mock)
LLM_PROVIDER=mock

# For real Groq API:
# LLM_PROVIDER=groq
# GROQ_API_KEY=your-groq-api-key
# Get free key: https://console.groq.com/keys
```

**Note:** Application works perfectly with zero configuration!

---

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=src/main/python/test_python_app --cov-report=html
```

### API Testing

See `docs/api-testing/` for:
- Automated test script
- Postman collection
- cURL command reference

---

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: SQLAlchemy 2.0 + SQLite/PostgreSQL
- **LLM**: Groq API (Llama 3.1 8B Instant)
- **Testing**: pytest + pytest-asyncio + pytest-cov
- **HTTP Client**: httpx (async)
- **Validation**: Pydantic 2.5

---

## 📊 Data Model

```
User (1) ──────< Conversations (many)
  │
  └────────────< Documents (many)

Conversation (1) ──< Messages (many)
       │
       └──────────>< Documents (many-to-many via RAG)

Document (1) ────< DocumentChunks (many)
```

**Tables**: Users, Conversations, Messages, Documents, DocumentChunks, ConversationDocuments

---

## 🚢 Deployment

### Simple Deployment

The application runs with a single command:

```bash
python3 local_start.py
```

### Production Considerations

- Set `LLM_PROVIDER=groq` with valid API key
- Use PostgreSQL instead of SQLite for better concurrency
- Configure proper logging levels
- Set up monitoring (health checks at `/health`)
- Use a reverse proxy (nginx) for HTTPS
- Configure rate limiting
- Set up database backups
- Use a process manager (systemd, supervisor) to keep it running

---

## 📚 Documentation

Additional documentation in `docs/`:

- **`docs/guides/`** - Detailed guides
  - ARCHITECTURE.md - Design decisions and scalability
  - API_EXAMPLES.md - Detailed API usage examples
  - PROJECT_SUMMARY.md - Complete feature overview
  - And more...

- **`docs/api-testing/`** - Testing resources
  - TEST_API.sh - Automated test script
  - Postman collection - GUI testing
  - cURL commands - Manual testing

---

## 🎯 Quick Examples

### Create User and Start Chat

```bash
# 1. Create user
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com"}'

# 2. Start conversation (use user_id from above)
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID",
    "first_message": "Hello! Tell me about Python.",
    "mode": "open_chat"
  }'
```

### RAG Conversation with Document

```bash
# 1. Upload document
curl -X POST http://localhost:8000/api/documents \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID",
    "filename": "python_guide.txt",
    "content": "Python is a programming language created by Guido van Rossum in 1991...",
    "mime_type": "text/plain"
  }'

# 2. Create RAG conversation (use document_id from above)
curl -X POST http://localhost:8000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "USER_ID",
    "first_message": "Who created Python?",
    "mode": "grounded_rag",
    "document_ids": ["DOCUMENT_ID"]
  }'
```

---

## 🤝 Contributing

This project was built as part of the BOT Consulting Associate AI Software Engineer case study.

---

## 📄 License

MIT License

---

## 🚀 Getting Started Checklist

- [ ] Start server: `python3 local_start.py`
- [ ] Open API docs: http://localhost:8000/api/docs
- [ ] Create a user via Swagger UI
- [ ] Start a conversation
- [ ] Upload a document
- [ ] Try RAG conversation
- [ ] Run tests: `pytest`

---

## 📞 Support

For questions or issues, please check the documentation in `docs/guides/` or open an issue.

---

**Built with FastAPI, SQLAlchemy, and modern Python best practices** 🐍✨
