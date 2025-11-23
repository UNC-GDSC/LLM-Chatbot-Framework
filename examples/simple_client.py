#!/usr/bin/env python3
"""Simple example client for the LLM Chatbot Framework."""

import requests
from typing import Optional


class SimpleChatbotClient:
    """Simple client for interacting with the chatbot API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the client.

        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url
        self.token: Optional[str] = None
        self.conversation_id: Optional[str] = None

    def register(self, email: str, username: str, password: str) -> dict:
        """Register a new user.

        Args:
            email: User email
            username: Username
            password: Password

        Returns:
            User data
        """
        response = requests.post(
            f"{self.base_url}/api/v1/auth/register",
            json={"email": email, "username": username, "password": password},
        )
        response.raise_for_status()
        return response.json()

    def login(self, username: str, password: str) -> str:
        """Login and get access token.

        Args:
            username: Username
            password: Password

        Returns:
            Access token
        """
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return self.token

    def chat(self, message: str, new_conversation: bool = False) -> str:
        """Send a chat message and get response.

        Args:
            message: Message to send
            new_conversation: Start a new conversation

        Returns:
            Assistant's response
        """
        if not self.token:
            raise ValueError("Not logged in. Call login() first.")

        headers = {"Authorization": f"Bearer {self.token}"}
        data = {"message": message}

        if not new_conversation and self.conversation_id:
            data["conversation_id"] = self.conversation_id

        response = requests.post(
            f"{self.base_url}/api/v1/chat/message", json=data, headers=headers
        )
        response.raise_for_status()

        result = response.json()
        self.conversation_id = result["conversation_id"]
        return result["message"]["content"]

    def get_history(self) -> list:
        """Get conversation history.

        Returns:
            List of messages
        """
        if not self.token:
            raise ValueError("Not logged in. Call login() first.")

        if not self.conversation_id:
            return []

        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/api/v1/chat/conversations/{self.conversation_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()["messages"]


def main():
    """Example usage of the chatbot client."""
    client = SimpleChatbotClient()

    # Register (comment out if already registered)
    try:
        print("Registering user...")
        client.register("demo@example.com", "demouser", "demopass123")
        print("✓ User registered successfully")
    except requests.exceptions.HTTPError:
        print("User already exists, continuing...")

    # Login
    print("\nLogging in...")
    client.login("demouser", "demopass123")
    print("✓ Logged in successfully")

    # Start conversation
    print("\n--- Starting Chat ---\n")

    # First message
    response = client.chat("What is Python?", new_conversation=True)
    print(f"You: What is Python?")
    print(f"Assistant: {response}\n")

    # Follow-up message
    response = client.chat("What are its main features?")
    print(f"You: What are its main features?")
    print(f"Assistant: {response}\n")

    # Get conversation history
    print("--- Conversation History ---")
    history = client.get_history()
    for i, msg in enumerate(history, 1):
        print(f"{i}. [{msg['role']}]: {msg['content'][:100]}...")


if __name__ == "__main__":
    main()
