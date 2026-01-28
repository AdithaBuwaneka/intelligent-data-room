"""
Query Router

Handles chat queries using the multi-agent system (Planner + Executor).
Includes intelligent query classification to handle greetings and casual chat.

INTELLIGENT ANALYSIS (Gemini 2.5):
- QueryAnalyzer validates queries BEFORE expensive processing
- Filters meaningless queries ("pp", "test", "fdsf", "5")
- Determines visualization needs intelligently
- Extracts limit numbers (top 5, top 10)
- Identifies correct columns for charts
"""

import gc
import time
import pandas as pd
import httpx
from io import BytesIO
from fastapi import APIRouter, HTTPException

from app.models.schemas import QueryRequest, QueryResponse, ChatMessage
from app.services.database import get_database
from app.services.memory import get_memory_service
from app.graph.workflow import AgentWorkflow
from app.agents.classifier import get_classifier
from app.agents.query_analyzer import get_query_analyzer

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
    Load a DataFrame from a remote URL with memory optimization.

    Args:
        file_url: URL to the CSV/XLSX file

    Returns:
        Pandas DataFrame
    """
    content = None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(file_url, timeout=30.0)
            response.raise_for_status()

            content = response.content

            # Determine file type from URL
            if file_url.lower().endswith(".xlsx") or file_url.lower().endswith(".xls"):
                df = pd.read_excel(BytesIO(content))
            else:
                # Default to CSV with memory optimization
                df = pd.read_csv(BytesIO(content), low_memory=True)

            return df

    except Exception as e:
        print(f"❌ Error loading file from URL: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to load data file: {str(e)}",
        )
    finally:
        # Clean up response content from memory
        if content is not None:
            del content
            gc.collect()


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query about the uploaded data.

    Multi-Agent Workflow:
    1. Load last 5 messages for context
    2. Classify query (data question vs greeting/chitchat)
    3. If greeting/chitchat: Return friendly response
    4. If data question: Load data and run Planner + Executor workflow
    5. Store conversation in MongoDB

    Returns:
        QueryResponse with answer, execution plan, and optional chart configuration
    """
    start_time = time.time()

    # Get services
    memory = await get_memory_service()
    classifier = get_classifier()

    try:
        # Step 1: Get conversation context
        context = await memory.get_context_for_agent(request.session_id)
        print(f"📚 Context loaded: {len(context)} chars")

        # Step 2: Intelligently classify the query using AI
        # Let the AI handle ALL messages - greetings, chitchat, data questions, follow-ups
        has_data_context = "[executed data analysis]" in context or "[created chart]" in context
        print(f"🔍 Question: '{request.question}' | Has data context: {has_data_context}")
        
        query_type = await classifier.classify(request.question, context)
        print(f"🤖 AI classified as: {query_type}")

        # Step 3: Handle non-data queries (greetings, chitchat)
        if query_type in ["GREETING", "CHITCHAT"]:
            friendly_response = classifier.get_friendly_response(query_type, request.question)

            # Save user message
            await memory.save_message(
                session_id=request.session_id,
                role="user",
                content=request.question,
            )

            # Save assistant response
            await memory.save_message(
                session_id=request.session_id,
                role="assistant",
                content=friendly_response,
                plan=None,
                chart_config=None,
            )

            execution_time = time.time() - start_time
            print(f"⏱️ Friendly response time: {execution_time:.2f}s")

            return QueryResponse(
                answer=friendly_response,
                plan=None,
                chart_config=None,
                execution_time=execution_time,
            )

        # Step 4: For DATA_QUESTION or UNCLEAR - run full workflow
        workflow = get_workflow()

        # Load DataFrame from file URL
        df = await load_dataframe_from_url(request.file_url)
        print(f"📊 Data loaded: {len(df)} rows, {len(df.columns)} columns")

        # Step 4.5: INTELLIGENT QUERY ANALYSIS (Gemini 2.5)
        # Validates query and extracts parameters BEFORE expensive processing
        query_analyzer = get_query_analyzer()

        # Build schema for analysis
        data_schema = {
            "columns": df.columns.tolist(),
            "sample_data": {col: str(df[col].dropna().iloc[0])[:50] if len(df[col].dropna()) > 0 else "N/A"
                          for col in df.columns},
            "row_count": len(df),
        }

        # Get previous analysis for follow-up handling
        previous_analysis = await memory.get_last_query_analysis(request.session_id)

        query_analysis = await query_analyzer.analyze(
            question=request.question,
            schema=data_schema,
            context=context,
        )

        # FOLLOW-UP HANDLING: Merge previous analysis when needed
        if query_analysis.is_follow_up and query_analysis.inherit_from_previous and previous_analysis:
            print(f"🔄 Follow-up detected: {query_analysis.follow_up_type}")

            # Inherit from previous analysis what wasn't specified
            if not query_analysis.group_column and previous_analysis.get("group_column"):
                query_analysis.group_column = previous_analysis["group_column"]
            if not query_analysis.value_column and previous_analysis.get("value_column"):
                query_analysis.value_column = previous_analysis["value_column"]
            if not query_analysis.aggregation and previous_analysis.get("aggregation"):
                query_analysis.aggregation = previous_analysis["aggregation"]

            # For limit changes, keep other params
            if query_analysis.follow_up_type == "limit_change":
                if not query_analysis.chart_type and previous_analysis.get("chart_type"):
                    query_analysis.chart_type = previous_analysis["chart_type"]
                if previous_analysis.get("requires_visualization"):
                    query_analysis.requires_visualization = True

            # For chart type changes, keep the data params
            if query_analysis.follow_up_type == "chart_type_change":
                if not query_analysis.limit_number and previous_analysis.get("limit_number"):
                    query_analysis.limit_number = previous_analysis["limit_number"]
                query_analysis.requires_visualization = True

            print(f"🔄 Merged analysis: group={query_analysis.group_column}, "
                  f"value={query_analysis.value_column}, limit={query_analysis.limit_number}, "
                  f"chart={query_analysis.chart_type}")

        print(f"🧠 Query Analysis: meaningful={query_analysis.is_meaningful_query}, "
              f"can_answer={query_analysis.can_be_answered}, "
              f"viz={query_analysis.requires_visualization}, "
              f"limit={query_analysis.limit_number}, "
              f"follow_up={query_analysis.is_follow_up}")

        # FILTER: If query is not meaningful, return early with helpful message
        if not query_analysis.is_meaningful_query:
            response_msg = query_analysis.suggested_response or (
                "I couldn't understand your request. Please ask a clear question about your data, "
                "like 'What are the top 5 products by sales?' or 'Show total revenue by region'."
            )

            # Save messages
            await memory.save_message(
                session_id=request.session_id,
                role="user",
                content=request.question,
            )
            await memory.save_message(
                session_id=request.session_id,
                role="assistant",
                content=response_msg,
                plan=None,
                chart_config=None,
            )

            del df
            gc.collect()

            execution_time = time.time() - start_time
            return QueryResponse(
                answer=response_msg,
                plan=None,
                chart_config=None,
                execution_time=execution_time,
            )

        # Save user message
        await memory.save_message(
            session_id=request.session_id,
            role="user",
            content=request.question,
        )

        # Run multi-agent workflow with analysis context
        result = await workflow.run(
            question=request.question,
            dataframe=df,
            context=context,
            query_analysis=query_analysis,  # Pass analysis for intelligent decisions
        )

        # Save assistant message with query analysis for follow-up handling
        await memory.save_message(
            session_id=request.session_id,
            role="assistant",
            content=result["answer"],
            plan=result["plan"],
            chart_config=result["chart_config"],
            query_analysis=query_analysis.model_dump() if query_analysis else None,
        )

        # Clean up DataFrame from memory
        del df
        gc.collect()

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
    finally:
        # Always clean up memory
        gc.collect()


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

    Deletes all messages and uploaded files for the given session.
    """
    try:
        from app.services.database import get_database
        
        memory = await get_memory_service()
        deleted_count = await memory.clear_session(session_id)
        
        # Also delete uploaded files for this session
        db = await get_database()
        file_result = await db.files_collection.delete_many(
            {"session_id": session_id}
        )

        return {
            "session_id": session_id,
            "deleted_count": deleted_count,
            "files_deleted": file_result.deleted_count,
            "message": "Chat history and files cleared successfully",
        }

    except Exception as e:
        print(f"❌ Clear history error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear chat history: {str(e)}",
        )


@router.get("/sessions")
async def list_sessions():
    """
    List all chat sessions.

    Returns a list of sessions with their IDs, first message, and message count.
    Sessions are ordered by most recent first.
    """
    try:
        db = await get_database()

        # Use aggregation to get unique sessions with their first message and count
        pipeline = [
            # Group by session_id
            {
                "$group": {
                    "_id": "$session_id",
                    "first_message": {"$first": "$content"},
                    "first_timestamp": {"$min": "$timestamp"},
                    "last_timestamp": {"$max": "$timestamp"},
                    "message_count": {"$sum": 1},
                    "first_role": {"$first": "$role"},
                }
            },
            # Sort by last activity (most recent first)
            {"$sort": {"last_timestamp": -1}},
            # Limit to 20 sessions
            {"$limit": 20},
        ]

        cursor = db.messages_collection.aggregate(pipeline)
        sessions_data = await cursor.to_list(length=20)

        sessions = []
        for s in sessions_data:
            # Get first user message for preview
            first_user_msg = await db.messages_collection.find_one(
                {"session_id": s["_id"], "role": "user"},
                sort=[("timestamp", 1)]
            )
            
            preview = first_user_msg["content"][:50] if first_user_msg else "No messages"
            
            sessions.append({
                "session_id": s["_id"],
                "preview": preview + ("..." if first_user_msg and len(first_user_msg["content"]) > 50 else ""),
                "message_count": s["message_count"],
                "created_at": s["first_timestamp"].isoformat(),
                "last_activity": s["last_timestamp"].isoformat(),
            })

        return {
            "sessions": sessions,
            "count": len(sessions),
        }

    except Exception as e:
        print(f"❌ List sessions error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}",
        )

