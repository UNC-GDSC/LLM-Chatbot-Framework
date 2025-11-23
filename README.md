# LLM Chatbot Framework

A production-ready, lightweight Python backend for building local or cloud-based chatbots using FastAPI and LangChain.

## Features

- 🚀 **FastAPI Backend**: High-performance async API
- 🤖 **Multi-LLM Support**: OpenAI, Anthropic Claude, Ollama (local models)
- 💾 **Conversation Memory**: Persistent chat history with SQLite/PostgreSQL
- 🔐 **Authentication**: JWT-based auth with API key support
- ⚡ **WebSocket Streaming**: Real-time streaming responses
- 🛡️ **Rate Limiting**: Protect your API from abuse
- 🐳 **Docker Ready**: Easy deployment with Docker/Docker Compose
- 📊 **Monitoring**: Health checks and observability
- 🧪 **Comprehensive Tests**: Unit and integration tests included
- 📚 **OpenAPI Docs**: Auto-generated interactive API documentation

## Quick Start

### Prerequisites

- Python 3.9+
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd LLM-Chatbot-Framework
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

### Docker Deployment

```bash
docker-compose up --build
```

## Configuration

Key environment variables in `.env`:

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key
- `RATE_LIMIT_PER_MINUTE`: API rate limit

## API Endpoints

### Chat Endpoints
- `POST /api/v1/chat/message` - Send a message
- `POST /api/v1/chat/stream` - Stream responses (WebSocket)
- `GET /api/v1/chat/history/{conversation_id}` - Get conversation history
- `DELETE /api/v1/chat/conversation/{conversation_id}` - Delete conversation

### User Management
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token

### System
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## Architecture

```
app/
├── api/              # API routes and endpoints
├── core/             # Core configuration and settings
├── models/           # Database models
├── schemas/          # Pydantic schemas
├── services/         # Business logic
├── middleware/       # Custom middleware
└── utils/            # Utility functions
```

## LLM Providers

### OpenAI
```python
{
  "provider": "openai",
  "model": "gpt-4",
  "temperature": 0.7
}
```

### Anthropic Claude
```python
{
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 0.7
}
```

### Local (Ollama)
```python
{
  "provider": "ollama",
  "model": "llama2",
  "base_url": "http://localhost:11434"
}
```

## Testing

Run tests:
```bash
pytest
pytest --cov=app tests/  # With coverage
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions, please open a GitHub issue.
