# LLM Chatbot Framework v2.0 🚀

**A comprehensive, production-ready chatbot framework with RAG, file processing, analytics, and advanced features.**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ What's New in v2.0

### 🔥 Major Features Added

1. **RAG (Retrieval Augmented Generation)**
   - ChromaDB and FAISS vector database support
   - Document upload and automatic processing
   - Semantic search across your documents
   - Context-aware responses using your data

2. **File Upload & Processing**
   - Support for PDF, DOCX, TXT, MD, CSV, XLSX
   - Automatic document chunking and embedding
   - Per-user document collections
   - Document management API

3. **Advanced Analytics**
   - Token usage tracking
   - Cost estimation per request
   - Response latency monitoring
   - Provider and model statistics
   - Message feedback system (ratings & comments)

4. **Conversation Export**
   - Export to JSON, Markdown, PDF, or plain text
   - Beautiful PDF generation
   - Share-ready formats

5. **Conversation Sharing**
   - Generate shareable links
   - Optional expiration dates
   - View count tracking
   - Revocable links

6. **Redis Caching**
   - Response caching
   - Session management
   - Performance optimization

7. **Enhanced Security**
   - File upload validation
   - Rate limiting per endpoint
   - SQL injection protection
   - XSS prevention

## 📊 Complete Feature List

### Core Features

✅ **Multi-LLM Support**
- OpenAI (GPT-3.5, GPT-4, GPT-4 Turbo)
- Anthropic Claude (Claude 3.5 Sonnet, Opus)
- Ollama (Llama 2, Mistral, and 50+ local models)

✅ **Conversation Management**
- Persistent chat history (SQLite/PostgreSQL)
- Multi-conversation support
- Conversation templates
- Search and filtering

✅ **Authentication & Security**
- JWT tokens (access + refresh)
- Password hashing (bcrypt)
- API key management
- Role-based access control

✅ **Real-time Communication**
- WebSocket streaming
- Server-Sent Events (SSE)
- Token-by-token responses
- Progress indicators

✅ **Database Layer**
- SQLAlchemy ORM
- Async operations
- Migration support (Alembic)
- Multi-database support

✅ **Production Features**
- Docker & Docker Compose
- Health checks
- Prometheus metrics
- Structured logging
- Error tracking (Sentry)
- Rate limiting
- CORS configuration

## 🎯 API Endpoints

### Authentication
```
POST   /api/v1/auth/register      - Register new user
POST   /api/v1/auth/login         - Login
POST   /api/v1/auth/refresh       - Refresh token
GET    /api/v1/auth/me            - Get current user
```

### Chat
```
POST   /api/v1/chat/message       - Send message
WS     /api/v1/chat/stream        - Stream responses
POST   /api/v1/chat/conversations - Create conversation
GET    /api/v1/chat/conversations - List conversations
GET    /api/v1/chat/conversations/{id} - Get conversation
PATCH  /api/v1/chat/conversations/{id} - Update conversation
DELETE /api/v1/chat/conversations/{id} - Delete conversation
```

### Documents & RAG 🆕
```
POST   /api/v1/documents/upload   - Upload document
GET    /api/v1/documents          - List documents
GET    /api/v1/documents/{id}     - Get document
POST   /api/v1/documents/{id}/process - Process document
DELETE /api/v1/documents/{id}     - Delete document
POST   /api/v1/documents/search   - Search in documents
```

### Analytics & Feedback 🆕
```
POST   /api/v1/analytics/feedback - Add message feedback
GET    /api/v1/analytics/usage    - Get usage statistics
GET    /api/v1/analytics/feedback/stats - Get feedback stats
```

### Export 🆕
```
GET    /api/v1/export/{id}/json     - Export as JSON
GET    /api/v1/export/{id}/markdown - Export as Markdown
GET    /api/v1/export/{id}/pdf      - Export as PDF
GET    /api/v1/export/{id}/text     - Export as plain text
```

### Sharing 🆕
```
POST   /api/v1/sharing/create          - Create share link
GET    /api/v1/sharing/view/{token}    - View shared conversation
DELETE /api/v1/sharing/{token}         - Revoke share link
GET    /api/v1/sharing/conversation/{id} - Get conversation shares
```

### System
```
GET    /health  - Health check
GET    /metrics - Prometheus metrics
GET    /docs    - API documentation
```

## 🚀 Quick Start

### 1. Install

```bash
# Clone repository
git clone <repo-url>
cd LLM-Chatbot-Framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your settings
```

Add your API keys:
```env
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key

# Enable features
ENABLE_RAG=true
ENABLE_FILE_UPLOAD=true
ENABLE_ANALYTICS=true
ENABLE_EXPORTS=true
ENABLE_CONVERSATION_SHARING=true
```

### 3. Run

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for interactive documentation!

### With Docker

```bash
docker-compose up -d
```

## 📖 Usage Examples

### RAG with Document Upload

```python
import requests

# Upload a document
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/documents/upload',
        files={'file': f},
        headers={'Authorization': f'Bearer {token}'},
        params={'process_now': True}
    )

doc_id = response.json()['id']

# Search in documents
response = requests.post(
    'http://localhost:8000/api/v1/documents/search',
    json={'query': 'What is the main topic?', 'k': 4},
    headers={'Authorization': f'Bearer {token}'}
)

results = response.json()['results']
for result in results:
    print(f"Score: {result['score']}")
    print(f"Content: {result['content']}\n")
```

### Export Conversation

```python
# Export as PDF
response = requests.get(
    f'http://localhost:8000/api/v1/export/{conversation_id}/pdf',
    headers={'Authorization': f'Bearer {token}'}
)

with open('conversation.pdf', 'wb') as f:
    f.write(response.content)
```

### Share Conversation

```python
# Create share link
response = requests.post(
    'http://localhost:8000/api/v1/sharing/create',
    json={
        'conversation_id': conversation_id,
        'expires_in_days': 7
    },
    headers={'Authorization': f'Bearer {token}'}
)

share_url = response.json()['share_url']
print(f"Share link: {share_url}")
```

### Get Usage Statistics

```python
response = requests.get(
    'http://localhost:8000/api/v1/analytics/usage',
    headers={'Authorization': f'Bearer {token}'}
)

stats = response.json()
print(f"Total tokens used: {stats['total_tokens']}")
print(f"Total cost: ${stats['total_cost']}")
print(f"Average latency: {stats['average_latency_ms']}ms")
```

## 🎨 Frontend Example

A simple HTML/JS frontend is included in `frontend/index.html`:

```bash
# Serve the frontend
python -m http.server 8080 --directory frontend
```

Visit http://localhost:8080

## 📦 Project Structure

```
LLM-Chatbot-Framework/
├── app/
│   ├── api/v1/              # API endpoints
│   │   ├── auth.py          # Authentication
│   │   ├── chat.py          # Chat operations
│   │   ├── documents.py     # Document upload & RAG 🆕
│   │   ├── analytics.py     # Analytics & feedback 🆕
│   │   ├── exports.py       # Export functionality 🆕
│   │   └── sharing.py       # Conversation sharing 🆕
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings (enhanced) 🔄
│   │   ├── database.py      # Database setup
│   │   ├── cache.py         # Redis cache 🆕
│   │   ├── security.py      # Security utilities
│   │   └── logging.py       # Logging config
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── analytics.py     # New models 🆕
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py
│   │   ├── chat.py
│   │   └── documents.py     # New schemas 🆕
│   ├── services/            # Business logic
│   │   ├── llm_service.py
│   │   ├── chat_service.py
│   │   ├── user_service.py
│   │   ├── document_service.py  # 🆕
│   │   ├── analytics_service.py # 🆕
│   │   ├── export_service.py    # 🆕
│   │   ├── sharing_service.py   # 🆕
│   │   └── rag/             # RAG services 🆕
│   │       └── rag_service.py
│   ├── middleware/          # Middleware
│   ├── utils/               # Utilities
│   └── main.py              # Application entry (enhanced) 🔄
├── tests/                   # Test suite
├── frontend/                # Simple frontend example 🆕
├── alembic/                 # Database migrations 🆕
├── uploads/                 # Uploaded files 🆕
├── vector_db/               # Vector database 🆕
└── docs/                    # Documentation
```

## 🔧 Configuration

### Enhanced .env Options

```env
# RAG Settings
VECTOR_DB_TYPE=chromadb  # chromadb or faiss
VECTOR_DB_PATH=./vector_db
EMBEDDING_MODEL=text-embedding-ada-002
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
UPLOAD_DIR=./uploads
ALLOWED_EXTENSIONS=[".pdf",".txt",".docx",".md"]

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_TTL=3600

# Analytics
ENABLE_ANALYTICS=true
TRACK_TOKEN_USAGE=true

# Features
ENABLE_RAG=true
ENABLE_FILE_UPLOAD=true
ENABLE_CONVERSATION_SHARING=true
ENABLE_EXPORTS=true
```

## 📊 Monitoring & Analytics

### Prometheus Metrics

Access at `/metrics`:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration
- `chat_requests_total` - Chat requests by provider/model
- `chat_tokens_total` - Token usage
- `errors_total` - Error counts

### Usage Analytics

Track and analyze:
- Token usage per user/model
- Cost estimation
- Response latency
- Popular models
- Conversation patterns

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific tests
pytest tests/test_documents.py
pytest tests/test_analytics.py
```

## 🚀 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment guides:

- AWS (ECS, EC2, Lambda)
- Google Cloud (Cloud Run, GKE)
- Azure (Container Instances, AKS)
- Heroku, Railway, DigitalOcean

### Docker Production

```bash
docker build -t chatbot-api:v2.0 .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -e DATABASE_URL=postgresql://... \
  chatbot-api:v2.0
```

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md)
- [API Examples](EXAMPLES.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Contributing](CONTRIBUTING.md)
- [API Documentation](http://localhost:8000/docs)

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🆕 Changelog

### v2.0.0 (Latest)
- ✨ Added RAG with ChromaDB/FAISS support
- ✨ Document upload and processing (PDF, DOCX, TXT, MD)
- ✨ Advanced analytics and usage tracking
- ✨ Message feedback system
- ✨ Conversation export (JSON, MD, PDF, TXT)
- ✨ Conversation sharing with expirable links
- ✨ Redis caching layer
- ✨ Enhanced security and validation
- ✨ Frontend example
- 🔄 Enhanced configuration system
- 🔄 Improved error handling
- 📚 Comprehensive documentation updates

### v1.0.0
- Initial release
- Basic chatbot functionality
- Multi-LLM support
- Authentication system

## 🙋 Support

- GitHub Issues: Report bugs and request features
- Documentation: Check our comprehensive guides
- API Docs: Interactive docs at `/docs`

## ⭐ Show Your Support

Give a ⭐️ if this project helped you!

---

Built with ❤️ using FastAPI and LangChain
