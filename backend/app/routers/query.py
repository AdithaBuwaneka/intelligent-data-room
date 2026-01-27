"""
Query Router

Handles chat queries using the multi-agent system (Planner + Executor).
"""

import time
import pandas as pd
import httpx
from io import BytesIO
from fastapi import APIRouter, HTTPException

from app.models.schemas import QueryRequest, QueryResponse, ChatMessage
from app.services.database import get_database
from app.services.memory import get_memory_service
from app.graph.workflow import AgentWorkflow

router = APIRouter()

# Initialize workflow (singleton)
_workflow: AgentWorkflow | None = None


def get_workflow() -> AgentWorkflow:
    """Get or create workflow instance."""
    global _workflow
    if _workflow is None:
        _workflow = AgentWorkflow()
    return _workflow


async def load_dataframe_from_url(file_url: str) -> pd.DataFrame:
    """
    Load a DataFrame from a remote URL.

    Args:
        file_url: URL to the CSV/XLSX file

    Returns:
        Pandas DataFrame
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url, timeout=30.0)
            response.raise_for_status()

            content = response.content

            # Determine file type from URL
            if file_url.lower().endswith(".xlsx") or file_url.lower().endswith(".xls"):
                df = pd.read_excel(BytesIO(content))
            else:
                # Default to CSV
                df = pd.read_csv(BytesIO(content))

            return df

    except Exception as e:
        print(f"❌ Error loading file from URL: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load data file: {str(e)}",
        )


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query about the uploaded data.

    Multi-Agent Workflow:
    1. Load last 5 messages for context
    2. Load the data file from URL
    3. Planner Agent: Analyzes question + schema → Creates execution plan
    4. Executor Agent: Uses PandasAI to execute plan → Returns results
    5. Store conversation in MongoDB

    Returns:
        QueryResponse with answer, execution plan, and optional chart configuration
    """
    start_time = time.time()

    # Get services
    memory = await get_memory_service()
    workflow = get_workflow()

    try:
        # Step 1: Get conversation context
        context = await memory.get_context_for_agent(request.session_id)
        print(f"📚 Context loaded: {len(context)} chars")

        # Step 2: Load DataFrame from file URL
        df = await load_dataframe_from_url(request.file_url)
        print(f"📊 Data loaded: {len(df)} rows, {len(df.columns)} columns")

        # Step 3: Save user message
        await memory.save_message(
            session_id=request.session_id,
            role="user",
            content=request.question,
        )

        # Step 4: Run multi-agent workflow
        result = await workflow.run(
            question=request.question,
            dataframe=df,
            context=context,
        )

        # Step 5: Save assistant message
        await memory.save_message(
            session_id=request.session_id,
            role="assistant",
            content=result["answer"],
            plan=result["plan"],
            chart_config=result["chart_config"],
        )

        execution_time = time.time() - start_time
        print(f"⏱️ Total execution time: {execution_time:.2f}s")

        return QueryResponse(
            answer=result["answer"],
            plan=result["plan"],
            chart_config=result["chart_config"],
            execution_time=execution_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Query error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}",
        )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get chat history for a session.

    Returns all messages for the given session.
    """
    try:
        memory = await get_memory_service()
        messages = await memory.get_all_messages(session_id)

        return {
            "session_id": session_id,
            "messages": messages,
            "count": len(messages),
        }

    except Exception as e:
        print(f"❌ History error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat history: {str(e)}",
        )


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Clear chat history for a session.

    Deletes all messages for the given session.
    """
    try:
        memory = await get_memory_service()
        deleted_count = await memory.clear_session(session_id)

        return {
            "session_id": session_id,
            "deleted_count": deleted_count,
            "message": "Chat history cleared successfully",
        }

    except Exception as e:
        print(f"❌ Clear history error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear chat history: {str(e)}",
        )
