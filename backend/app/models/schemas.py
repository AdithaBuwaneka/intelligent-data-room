"""
Pydantic models for API request/response schemas.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class ChartConfig(BaseModel):
    """Configuration for frontend chart rendering."""

    type: str = Field(..., description="Chart type: bar, line, pie, scatter, area")
    data: list[dict[str, Any]] = Field(..., description="Chart data array")
    xKey: str = Field(..., description="Key for X-axis data")
    yKey: str | list[str] = Field(..., description="Key(s) for Y-axis data")
    title: Optional[str] = Field(None, description="Chart title")
    colors: Optional[list[str]] = Field(None, description="Custom color palette")


class FileUploadResponse(BaseModel):
    """Response after successful file upload."""

    file_id: str = Field(..., description="Unique file identifier")
    file_url: str = Field(..., description="URL to access the file")
    filename: str = Field(..., description="Original filename")
    columns: list[str] = Field(..., description="List of column names")
    row_count: int = Field(..., description="Number of rows in the dataset")
    session_id: str = Field(..., description="Session ID for this upload")


class QueryRequest(BaseModel):
    """Request body for chat queries."""

    session_id: str = Field(..., description="Session identifier")
    question: str = Field(..., description="User's natural language question")
    file_url: str = Field(..., description="URL of the uploaded data file")


class QueryResponse(BaseModel):
    """Response from the multi-agent query system."""

    answer: str = Field(..., description="Generated answer to the question")
    plan: Optional[str] = Field(None, description="Execution plan created by Planner agent")
    chart_config: Optional[ChartConfig] = Field(
        None, description="Chart configuration if visualization requested"
    )
    execution_time: Optional[float] = Field(
        None, description="Query execution time in seconds"
    )


class ChatMessage(BaseModel):
    """Chat message stored in MongoDB."""

    session_id: str = Field(..., description="Session identifier")
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    plan: Optional[str] = Field(None, description="Execution plan (for assistant)")
    chart_config: Optional[ChartConfig] = Field(
        None, description="Chart config (for assistant)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Message timestamp"
    )


class FileMetadata(BaseModel):
    """File metadata stored in MongoDB."""

    file_id: str = Field(..., description="Unique file identifier")
    session_id: str = Field(..., description="Session identifier")
    filename: str = Field(..., description="Original filename")
    file_url: str = Field(..., description="ImageKit URL")
    columns: list[str] = Field(..., description="Column names")
    row_count: int = Field(..., description="Number of rows")
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow, description="Upload timestamp"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
