# Usage Examples

This document provides practical examples of using the LLM Chatbot Framework API.

## Table of Contents
- [Authentication](#authentication)
- [Chat Operations](#chat-operations)
- [WebSocket Streaming](#websocket-streaming)
- [Python Client Examples](#python-client-examples)
- [JavaScript Client Examples](#javascript-client-examples)
- [cURL Examples](#curl-examples)

## Authentication

### Register a New User

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "username": "johndoe",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00"
}
```

### Login

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "securepassword123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Chat Operations

### Send a Message (New Conversation)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "message": "What is machine learning?"
  }'
```

**Response:**
```json
{
  "conversation_id": "conv-123",
  "message": {
    "id": "msg-456",
    "role": "assistant",
    "content": "Machine learning is a subset of artificial intelligence...",
    "tokens": null,
    "created_at": "2024-01-01T12:00:00"
  },
  "model_config": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 2000,
    "stream": false
  }
}
```

### Send a Message (Existing Conversation)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "message": "Can you explain that in simpler terms?",
    "conversation_id": "conv-123"
  }'
```

### Send a Message with Custom Model

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "message": "Write a Python function to sort a list",
    "model_config": {
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "temperature": 0.5,
      "max_tokens": 1500
    }
  }'
```

### Create a Conversation

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/chat/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Python Programming Help"
  }'
```

### Get All Conversations

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/chat/conversations \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response:**
```json
[
  {
    "id": "conv-123",
    "user_id": "user-456",
    "title": "Python Programming Help",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:05:00",
    "message_count": 4,
    "messages": []
  }
]
```

### Get Conversation with Messages

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/chat/conversations/conv-123 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update Conversation Title

**Request:**
```bash
curl -X PATCH http://localhost:8000/api/v1/chat/conversations/conv-123 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Advanced Python Concepts"
  }'
```

### Delete a Conversation

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/chat/conversations/conv-123 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## WebSocket Streaming

### JavaScript WebSocket Example

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/stream');

// Authenticate
ws.onopen = () => {
  ws.send(JSON.stringify({
    token: 'YOUR_ACCESS_TOKEN'
  }));

  // Send message
  ws.send(JSON.stringify({
    message: 'Explain quantum computing',
    model_config: {
      provider: 'openai',
      model: 'gpt-4',
      temperature: 0.7
    }
  }));
};

// Handle messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'conversation_id') {
    console.log('Conversation ID:', data.conversation_id);
  } else if (data.type === 'chunk') {
    process.stdout.write(data.content); // Stream chunks
  } else if (data.type === 'complete') {
    console.log('\nResponse complete');
  } else if (data.error) {
    console.error('Error:', data.error);
  }
};
```

## Python Client Examples

### Basic Client

```python
import requests
from typing import Optional

class ChatbotClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None

    def register(self, email: str, username: str, password: str):
        """Register a new user."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password
            }
        )
        response.raise_for_status()
        return response.json()

    def login(self, username: str, password: str):
        """Login and store token."""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data

    def send_message(self, message: str, conversation_id: Optional[str] = None):
        """Send a chat message."""
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"message": message}
        if conversation_id:
            data["conversation_id"] = conversation_id

        response = requests.post(
            f"{self.base_url}/api/v1/chat/message",
            json=data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    def get_conversations(self):
        """Get all conversations."""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/api/v1/chat/conversations",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

# Usage
client = ChatbotClient()

# Register and login
client.register("user@example.com", "johndoe", "password123")
client.login("johndoe", "password123")

# Send a message
result = client.send_message("What is artificial intelligence?")
print(f"Response: {result['message']['content']}")

# Continue conversation
result = client.send_message(
    "Tell me more",
    conversation_id=result['conversation_id']
)
print(f"Response: {result['message']['content']}")
```

### Async Client

```python
import asyncio
import aiohttp

class AsyncChatbotClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = None

    async def login(self, username: str, password: str):
        """Login and store token."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": username, "password": password}
            ) as response:
                data = await response.json()
                self.token = data["access_token"]
                return data

    async def send_message(self, message: str, conversation_id=None):
        """Send a chat message."""
        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"message": message}
        if conversation_id:
            data["conversation_id"] = conversation_id

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/chat/message",
                json=data,
                headers=headers
            ) as response:
                return await response.json()

# Usage
async def main():
    client = AsyncChatbotClient()
    await client.login("johndoe", "password123")

    result = await client.send_message("Hello, how are you?")
    print(result['message']['content'])

asyncio.run(main())
```

## JavaScript Client Examples

### Fetch API Client

```javascript
class ChatbotClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.token = null;
  }

  async register(email, username, password) {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password })
    });
    return response.json();
  }

  async login(username, password) {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    this.token = data.access_token;
    return data;
  }

  async sendMessage(message, conversationId = null) {
    const body = { message };
    if (conversationId) body.conversation_id = conversationId;

    const response = await fetch(`${this.baseUrl}/api/v1/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`
      },
      body: JSON.stringify(body)
    });
    return response.json();
  }

  async getConversations() {
    const response = await fetch(`${this.baseUrl}/api/v1/chat/conversations`, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    return response.json();
  }
}

// Usage
const client = new ChatbotClient();
await client.login('johndoe', 'password123');
const result = await client.sendMessage('Hello!');
console.log(result.message.content);
```

## cURL Examples

### Complete Workflow

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"testpass123"}'

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' \
  | jq -r '.access_token')

# 3. Send message
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"What is the capital of France?"}'

# 4. Get conversations
curl -X GET http://localhost:8000/api/v1/chat/conversations \
  -H "Authorization: Bearer $TOKEN"

# 5. Health check
curl http://localhost:8000/health
```

## Error Handling

All API endpoints return standard error responses:

```json
{
  "detail": "Error message",
  "timestamp": "2024-01-01T12:00:00"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
