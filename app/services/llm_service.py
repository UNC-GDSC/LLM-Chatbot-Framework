"""LLM service for managing different language model providers."""

from typing import Optional, AsyncIterator
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.chat import ModelConfig

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with various LLM providers."""

    def __init__(self) -> None:
        """Initialize LLM service."""
        self.providers = {
            "openai": self._get_openai_model,
            "anthropic": self._get_anthropic_model,
            "ollama": self._get_ollama_model,
        }

    def _get_openai_model(self, config: ModelConfig) -> ChatOpenAI:
        """Get OpenAI chat model."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")

        return ChatOpenAI(
            model_name=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            openai_api_key=settings.OPENAI_API_KEY,
            streaming=config.stream,
        )

    def _get_anthropic_model(self, config: ModelConfig) -> ChatAnthropic:
        """Get Anthropic chat model."""
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set")

        return ChatAnthropic(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            anthropic_api_key=settings.ANTHROPIC_API_KEY,
            streaming=config.stream,
        )

    def _get_ollama_model(self, config: ModelConfig) -> Ollama:
        """Get Ollama model for local inference."""
        return Ollama(
            model=config.model,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=config.temperature,
        )

    def get_model(self, config: ModelConfig) -> any:
        """Get the appropriate model based on configuration."""
        provider_func = self.providers.get(config.provider.lower())
        if not provider_func:
            raise ValueError(f"Unsupported provider: {config.provider}")

        logger.info(f"Initializing {config.provider} model: {config.model}")
        return provider_func(config)

    async def generate_response(
        self,
        messages: list,
        config: ModelConfig,
    ) -> str:
        """Generate a response from the LLM."""
        try:
            model = self.get_model(config)

            # Convert message history to LangChain format
            langchain_messages = []
            for msg in messages:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))

            # Generate response
            if config.provider == "ollama":
                # Ollama uses different API
                prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                response = await model.ainvoke(prompt)
            else:
                response = await model.ainvoke(langchain_messages)

            # Extract content based on response type
            if hasattr(response, "content"):
                return response.content
            else:
                return str(response)

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    async def generate_stream(
        self,
        messages: list,
        config: ModelConfig,
    ) -> AsyncIterator[str]:
        """Generate a streaming response from the LLM."""
        try:
            config.stream = True
            model = self.get_model(config)

            # Convert message history to LangChain format
            langchain_messages = []
            for msg in messages:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))

            # Stream response
            async for chunk in model.astream(langchain_messages):
                if hasattr(chunk, "content"):
                    yield chunk.content
                else:
                    yield str(chunk)

        except Exception as e:
            logger.error(f"Error generating streaming response: {str(e)}")
            raise
