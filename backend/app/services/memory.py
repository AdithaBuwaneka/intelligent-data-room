"""
Memory Service

Handles chat history and context retention using MongoDB.
Stores and retrieves messages for follow-up question handling.
"""

from datetime import datetime
from typing import Optional

from app.services.database import get_database
from app.config import get_settings


class MemoryService:
    """
    Chat memory and context management.

    Responsibilities:
    - Store chat messages (user + assistant)
    - Retrieve last N messages for context
    - Format context for agents
    """

    def __init__(self):
        self.settings = get_settings()

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        plan: Optional[str] = None,
        chart_config: Optional[dict] = None,
        query_analysis: Optional[dict] = None,
    ) -> str:
        """
        Save a message to chat history.

        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            plan: Execution plan (for assistant messages)
            chart_config: Chart configuration (for assistant messages)
            query_analysis: QueryAnalysis dict for follow-up reference

        Returns:
            Inserted message ID
        """
        db = await get_database()

        message = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "plan": plan,
            "chart_config": chart_config,
            "query_analysis": query_analysis,  # Store for follow-up handling
            "timestamp": datetime.utcnow(),
        }

        result = await db.messages_collection.insert_one(message)
        return str(result.inserted_id)

    async def get_last_n_messages(
        self,
        session_id: str,
        n: Optional[int] = None,
    ) -> list[dict]:
        """
        Retrieve the last N messages for a session.

        Args:
            session_id: Session identifier
            n: Number of messages to retrieve (default from settings)

        Returns:
            List of messages ordered by timestamp (oldest first)
        """
        db = await get_database()

        if n is None:
            n = self.settings.max_context_messages

        cursor = db.messages_collection.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(n)

        messages = await cursor.to_list(length=n)

        # Reverse to get chronological order (oldest first)
        messages.reverse()

        # Convert ObjectId to string and format
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": str(msg["_id"]),
                "role": msg["role"],
                "content": msg["content"],
                "plan": msg.get("plan"),
                "chart_config": msg.get("chart_config"),
                "timestamp": msg["timestamp"].isoformat(),
            })

        return formatted_messages

    async def get_context_for_agent(
        self,
        session_id: str,
    ) -> str:
        """
        Get formatted context string for the Planner agent.

        Args:
            session_id: Session identifier

        Returns:
            Formatted context string with conversation history
        """
        messages = await self.get_last_n_messages(session_id)

        if not messages:
            return "No previous conversation context."

        # Check if there was data analysis in the conversation
        has_data_analysis = any(
            msg.get("plan") or msg.get("chart_config")
            for msg in messages
        )

        context_lines = []

        # Add a header indicating data analysis context
        if has_data_analysis:
            context_lines.append("[DATA ANALYSIS SESSION - Previous messages involved data queries]")

        context_lines.append("Previous conversation:")

        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg['content']

            # Add indicators for data analysis responses
            if msg.get("plan"):
                content += " [executed data analysis]"
            if msg.get("chart_config"):
                chart = msg.get("chart_config", {})
                chart_type = chart.get("type", "unknown")
                content += f" [created {chart_type} chart]"

            # Add query analysis details for follow-up handling
            if msg.get("query_analysis"):
                qa = msg["query_analysis"]
                analysis_parts = []
                if qa.get("group_column"):
                    analysis_parts.append(f"grouped by {qa['group_column']}")
                if qa.get("value_column"):
                    analysis_parts.append(f"value: {qa['value_column']}")
                if qa.get("aggregation"):
                    analysis_parts.append(f"aggregation: {qa['aggregation']}")
                if qa.get("limit_number"):
                    analysis_parts.append(f"limit: {qa['limit_number']}")
                if qa.get("chart_type"):
                    analysis_parts.append(f"chart: {qa['chart_type']}")
                if analysis_parts:
                    content += f" [analysis: {', '.join(analysis_parts)}]"

            context_lines.append(f"{role}: {content}")

        return "\n".join(context_lines)

    async def get_last_query_analysis(self, session_id: str) -> Optional[dict]:
        """
        Get the most recent QueryAnalysis for follow-up handling.

        Args:
            session_id: Session identifier

        Returns:
            QueryAnalysis dict or None
        """
        db = await get_database()

        # Find most recent message with query_analysis
        cursor = db.messages_collection.find(
            {
                "session_id": session_id,
                "query_analysis": {"$ne": None}
            }
        ).sort("timestamp", -1).limit(1)

        messages = await cursor.to_list(length=1)

        if messages and messages[0].get("query_analysis"):
            return messages[0]["query_analysis"]

        return None

    async def clear_session(self, session_id: str) -> int:
        """
        Clear all messages for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of deleted messages
        """
        db = await get_database()

        result = await db.messages_collection.delete_many(
            {"session_id": session_id}
        )

        return result.deleted_count

    async def get_all_messages(self, session_id: str) -> list[dict]:
        """
        Get all messages for a session (for chat history endpoint).

        Args:
            session_id: Session identifier

        Returns:
            List of all messages ordered by timestamp
        """
        db = await get_database()

        cursor = db.messages_collection.find(
            {"session_id": session_id}
        ).sort("timestamp", 1)

        messages = await cursor.to_list(length=1000)

        # Format messages
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": str(msg["_id"]),
                "session_id": msg["session_id"],
                "role": msg["role"],
                "content": msg["content"],
                "plan": msg.get("plan"),
                "chart_config": msg.get("chart_config"),
                "timestamp": msg["timestamp"],
            })

        return formatted_messages


# Global memory service instance
_memory_service: MemoryService | None = None


async def get_memory_service() -> MemoryService:
    """
    Get or create memory service instance.

    Returns:
        MemoryService instance
    """
    global _memory_service

    if _memory_service is None:
        _memory_service = MemoryService()

    return _memory_service
