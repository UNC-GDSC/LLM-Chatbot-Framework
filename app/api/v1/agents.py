"""LangChain Agents API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.security import get_current_user_id
from app.services.agent_service import AgentService

router = APIRouter()


class AgentRequest(BaseModel):
    """Request schema for agent execution."""

    query: str = Field(..., min_length=1, max_length=5000)
    tools: List[str] = Field(..., min_items=1)
    chat_history: Optional[List[dict]] = None
    model: str = Field(default="gpt-4")
    provider: str = Field(default="openai", pattern="^(openai|anthropic)$")


class AgentResponse(BaseModel):
    """Response schema for agent execution."""

    output: str
    intermediate_steps: List[dict]


class ToolsListResponse(BaseModel):
    """Response schema for available tools."""

    tools: List[str]


@router.get("/tools", response_model=ToolsListResponse)
async def list_available_tools() -> ToolsListResponse:
    """Get list of available agent tools."""
    agent_service = AgentService()
    tools = agent_service.get_tool_list()

    return ToolsListResponse(tools=tools)


@router.post("/execute", response_model=AgentResponse)
async def execute_agent(
    request: AgentRequest,
    user_id: str = Depends(get_current_user_id),
) -> AgentResponse:
    """Execute an agent with specified tools."""
    agent_service = AgentService()

    try:
        result = await agent_service.run_agent(
            query=request.query,
            tools=request.tools,
            chat_history=request.chat_history,
            model=request.model,
            provider=request.provider,
        )

        return AgentResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
