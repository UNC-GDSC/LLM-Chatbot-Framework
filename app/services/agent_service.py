"""LangChain Agents and Tools service for autonomous AI agents."""

from typing import List, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_openai_functions_agent, create_react_agent
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.tools import Tool, StructuredTool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.schema import SystemMessage, HumanMessage
import json
import asyncio

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentService:
    """Service for managing LangChain agents with various tools."""

    def __init__(self) -> None:
        """Initialize agent service."""
        self.available_tools = self._initialize_tools()

    def _initialize_tools(self) -> Dict[str, Tool]:
        """Initialize available tools for agents."""
        tools = {}

        # Web Search Tool
        try:
            search = DuckDuckGoSearchRun()
            tools["web_search"] = Tool(
                name="WebSearch",
                func=search.run,
                description="Search the web for current information. Use this when you need up-to-date information or facts.",
            )
        except Exception as e:
            logger.warning(f"Web search tool not available: {e}")

        # Calculator Tool
        def calculator(expression: str) -> str:
            """Evaluate a mathematical expression."""
            try:
                # Safe eval for basic math
                result = eval(expression, {"__builtins__": {}}, {})
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"

        tools["calculator"] = Tool(
            name="Calculator",
            func=calculator,
            description="Calculate mathematical expressions. Input should be a valid Python math expression.",
        )

        # JSON Parser Tool
        def json_parser(json_str: str) -> str:
            """Parse and format JSON."""
            try:
                data = json.loads(json_str)
                return json.dumps(data, indent=2)
            except Exception as e:
                return f"Error parsing JSON: {str(e)}"

        tools["json_parser"] = Tool(
            name="JSONParser",
            func=json_parser,
            description="Parse and format JSON strings. Useful for working with JSON data.",
        )

        # Text Analysis Tool
        def text_analyzer(text: str) -> str:
            """Analyze text properties."""
            words = text.split()
            chars = len(text)
            sentences = text.count('.') + text.count('!') + text.count('?')
            return json.dumps({
                "word_count": len(words),
                "character_count": chars,
                "sentence_count": sentences,
                "average_word_length": round(chars / len(words), 2) if words else 0,
            })

        tools["text_analyzer"] = Tool(
            name="TextAnalyzer",
            func=text_analyzer,
            description="Analyze text to get statistics like word count, character count, etc.",
        )

        return tools

    def get_tool_list(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.available_tools.keys())

    async def create_agent_executor(
        self,
        tools: List[str],
        model: str = "gpt-4",
        provider: str = "openai",
    ) -> AgentExecutor:
        """Create an agent executor with specified tools."""
        # Get LLM
        if provider == "openai":
            llm = ChatOpenAI(
                model=model,
                temperature=0,
                openai_api_key=settings.OPENAI_API_KEY,
            )
        elif provider == "anthropic":
            llm = ChatAnthropic(
                model=model,
                temperature=0,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Select requested tools
        selected_tools = []
        for tool_name in tools:
            if tool_name in self.available_tools:
                selected_tools.append(self.available_tools[tool_name])
            else:
                logger.warning(f"Tool {tool_name} not found")

        if not selected_tools:
            raise ValueError("No valid tools selected")

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant with access to various tools. Use them wisely to help the user."),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create agent
        if provider == "openai":
            agent = create_openai_functions_agent(llm, selected_tools, prompt)
        else:
            agent = create_react_agent(llm, selected_tools, prompt)

        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=selected_tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
        )

        return agent_executor

    async def run_agent(
        self,
        query: str,
        tools: List[str],
        chat_history: Optional[List[Dict[str, str]]] = None,
        model: str = "gpt-4",
        provider: str = "openai",
    ) -> Dict[str, Any]:
        """Run an agent with the given query and tools."""
        try:
            # Create agent executor
            agent_executor = await self.create_agent_executor(tools, model, provider)

            # Prepare chat history
            history = []
            if chat_history:
                for msg in chat_history:
                    if msg["role"] == "user":
                        history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        history.append(SystemMessage(content=msg["content"]))

            # Run agent
            result = await agent_executor.ainvoke({
                "input": query,
                "chat_history": history,
            })

            return {
                "output": result.get("output", ""),
                "intermediate_steps": [
                    {
                        "tool": step[0].tool,
                        "tool_input": step[0].tool_input,
                        "output": step[1],
                    }
                    for step in result.get("intermediate_steps", [])
                ],
            }

        except Exception as e:
            logger.error(f"Error running agent: {e}")
            raise


class CustomToolsManager:
    """Manager for custom user-defined tools."""

    def __init__(self) -> None:
        """Initialize custom tools manager."""
        self.custom_tools: Dict[str, Tool] = {}

    def add_tool(
        self,
        name: str,
        description: str,
        function_code: str,
    ) -> bool:
        """Add a custom tool (with security restrictions)."""
        try:
            # Create a restricted namespace for execution
            namespace = {
                "__builtins__": {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "sum": sum,
                    "max": max,
                    "min": min,
                }
            }

            # Execute function definition
            exec(function_code, namespace)

            # Get the function (assume it's named 'tool_function')
            if 'tool_function' in namespace:
                func = namespace['tool_function']

                # Create tool
                self.custom_tools[name] = Tool(
                    name=name,
                    func=func,
                    description=description,
                )

                logger.info(f"Added custom tool: {name}")
                return True

        except Exception as e:
            logger.error(f"Error adding custom tool: {e}")
            return False

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a custom tool by name."""
        return self.custom_tools.get(name)

    def list_tools(self) -> List[str]:
        """List all custom tools."""
        return list(self.custom_tools.keys())

    def remove_tool(self, name: str) -> bool:
        """Remove a custom tool."""
        if name in self.custom_tools:
            del self.custom_tools[name]
            logger.info(f"Removed custom tool: {name}")
            return True
        return False
