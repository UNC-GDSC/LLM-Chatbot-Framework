# Quick Start Guide

Get your LLM Chatbot Framework up and running in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- (Optional) Docker and Docker Compose

## Option 1: Local Development (Fastest)

### 1. Install Dependencies

```bash
# Clone the repository (if not already done)
cd LLM-Chatbot-Framework

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys (optional for getting started)
# You can start without API keys and add them later
```

For testing without LLM providers, the app will still work for authentication and conversation management.

### 3. Run the Application

```bash
# Start the server
uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000

### 4. Access the Documentation

Open your browser and visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Option 2: Docker (Production-like)

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 2. Start with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f app
```

The API will be available at: http://localhost:8000

### 3. Stop Services

```bash
docker-compose down
```

## Testing the API

### Using the Interactive Docs

1. Go to http://localhost:8000/docs
2. Click on "POST /api/v1/auth/register"
3. Click "Try it out"
4. Fill in the request body:
   ```json
   {
     "email": "test@example.com",
     "username": "testuser",
     "password": "testpass123"
   }
   ```
5. Click "Execute"

### Using cURL

```bash
# 1. Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}'

# Copy the access_token from the response

# 3. Send a chat message (replace YOUR_TOKEN with the access token)
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message":"Hello!"}'
```

### Using the Example Client

```bash
# Run the example client
python examples/simple_client.py
```

## Adding LLM Provider API Keys

To enable actual AI responses, add your API keys to the `.env` file:

### OpenAI

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4
```

Get your API key from: https://platform.openai.com/api-keys

### Anthropic Claude

```env
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_MODEL=claude-3-5-sonnet-20241022
```

Get your API key from: https://console.anthropic.com/

### Ollama (Local Models - Free!)

1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama2`
3. Configure in `.env`:
```env
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434
```

After adding API keys, restart the application.

## Common Commands

Using the Makefile:

```bash
make help          # Show available commands
make run           # Run development server
make test          # Run tests
make format        # Format code
make docker-up     # Start Docker containers
make docker-down   # Stop Docker containers
```

## Project Structure

```
LLM-Chatbot-Framework/
├── app/                    # Application code
│   ├── api/               # API endpoints
│   ├── core/              # Core configuration
│   ├── models/            # Database models
│   ├── schemas/           # Request/response schemas
│   ├── services/          # Business logic
│   └── main.py            # Application entry point
├── tests/                 # Test suite
├── examples/              # Example clients
├── docs/                  # Documentation
└── .env                   # Configuration (create from .env.example)
```

## Next Steps

1. **Read the Full Documentation**: Check out [README.md](README.md) for detailed features
2. **Explore the API**: Visit http://localhost:8000/docs for interactive documentation
3. **Run the Tests**: Execute `pytest` to run the test suite
4. **Deploy to Production**: See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment guides
5. **View Examples**: Check [EXAMPLES.md](EXAMPLES.md) for more usage examples

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Use a different port
uvicorn app.main:app --port 8001 --reload
```

### Database Locked Error

If using SQLite and getting database locked errors:

```bash
# Remove the database file and restart
rm chatbot.db
uvicorn app.main:app --reload
```

### Import Errors

Make sure you're in the virtual environment:

```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### API Key Not Working

1. Verify the API key is correct in `.env`
2. Restart the application after adding API keys
3. Check the logs for specific error messages

## Getting Help

- **Documentation**: See [README.md](README.md), [EXAMPLES.md](EXAMPLES.md), [DEPLOYMENT.md](DEPLOYMENT.md)
- **Issues**: Open an issue on GitHub
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## Success! 🎉

You now have a fully functional chatbot API running! Start building your chatbot applications.

Happy coding!
