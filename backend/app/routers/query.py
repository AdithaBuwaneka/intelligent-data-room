"""
Query Router

Handles chat queries using the multi-agent system (Planner + Executor).
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import QueryRequest, QueryResponse, ChatMessage

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query about the uploaded data.

    Multi-Agent Workflow:
    1. Load last 5 messages for context
    2. Planner Agent: Analyzes question + schema → Creates execution plan
    3. Executor Agent: Uses PandasAI to execute plan → Returns results
    4. Store conversation in MongoDB

    Returns answer, execution plan, and optional chart configuration.
    """
    # TODO: Implement in feature/07-query-endpoint
    raise HTTPException(
        status_code=501,
        detail="Query processing not yet implemented. Coming in feature/07-query-endpoint",
    )


@router.get("/history/{session_id}", response_model=list[ChatMessage])
async def get_chat_history(session_id: str):
    """
    Get chat history for a session.

    Returns the last N messages for context display.
    """
    # TODO: Implement in feature/09-context-retention
    raise HTTPException(
        status_code=501,
        detail="Chat history not yet implemented. Coming in feature/09-context-retention",
    )
