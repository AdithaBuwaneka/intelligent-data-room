"""
File Upload Router

Handles CSV/XLSX file uploads to ImageKit and stores metadata in MongoDB.
"""

import pandas as pd
from io import BytesIO
from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.config import get_settings
from app.models.schemas import FileUploadResponse
from app.services.database import get_database
from app.services.imagekit_service import get_imagekit_service

router = APIRouter()

# Allowed file types
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def validate_file(filename: str, content_type: str, file_size: int) -> None:
    """
    Validate uploaded file.

    Args:
        filename: Original filename
        content_type: MIME type
        file_size: File size in bytes

    Raises:
        HTTPException if validation fails
    """
    settings = get_settings()

    # Check file extension
    extension = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Check file size
    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
        )


def parse_dataframe(file_content: bytes, filename: str) -> pd.DataFrame:
    """
    Parse file content into a pandas DataFrame.

    Args:
        file_content: File bytes
        filename: Original filename (to determine parser)

    Returns:
        Parsed DataFrame

    Raises:
        HTTPException if parsing fails
    """
    try:
        extension = filename.split(".")[-1].lower()

        if extension == "csv":
            df = pd.read_csv(BytesIO(file_content))
        elif extension in ("xlsx", "xls"):
            df = pd.read_excel(BytesIO(file_content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        return df

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse file: {str(e)}",
        )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="CSV or XLSX file to upload"),
    session_id: str = Form(..., description="Session identifier"),
):
    """
    Upload a CSV or XLSX file for analysis.

    Process:
    1. Validate file type and size (max 10MB)
    2. Parse file to extract schema (columns, row count)
    3. Upload to ImageKit.io for cloud storage
    4. Store metadata in MongoDB

    Returns:
        FileUploadResponse with file metadata including URL and schema
    """
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Validate file
    validate_file(file.filename or "unknown", file.content_type or "", file_size)

    # Parse DataFrame to extract schema
    df = parse_dataframe(file_content, file.filename or "data.csv")

    columns = df.columns.tolist()
    row_count = len(df)

    # Generate unique file ID
    file_id = str(uuid4())

    # Upload to ImageKit
    imagekit = get_imagekit_service()
    upload_result = await imagekit.upload_file(
        file_content=file_content,
        filename=f"{file_id}_{file.filename}",
        folder="data-room",
    )

    file_url = upload_result["file_url"]

    # Store metadata in MongoDB
    db = await get_database()

    file_metadata = {
        "file_id": file_id,
        "imagekit_file_id": upload_result["file_id"],
        "session_id": session_id,
        "filename": file.filename,
        "file_url": file_url,
        "columns": columns,
        "row_count": row_count,
        "file_size": file_size,
        "content_type": file.content_type,
        "uploaded_at": datetime.utcnow(),
    }

    await db.files_collection.insert_one(file_metadata)

    print(f"✅ File uploaded: {file.filename} ({row_count} rows, {len(columns)} columns)")

    return FileUploadResponse(
        file_id=file_id,
        file_url=file_url,
        filename=file.filename or "unknown",
        columns=columns,
        row_count=row_count,
        session_id=session_id,
    )


@router.get("/file/{file_id}")
async def get_file_metadata(file_id: str):
    """
    Get metadata for an uploaded file.

    Args:
        file_id: Unique file identifier

    Returns:
        File metadata including URL and schema
    """
    db = await get_database()

    file_doc = await db.files_collection.find_one({"file_id": file_id})

    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")

    return {
        "file_id": file_doc["file_id"],
        "filename": file_doc["filename"],
        "file_url": file_doc["file_url"],
        "columns": file_doc["columns"],
        "row_count": file_doc["row_count"],
        "uploaded_at": file_doc["uploaded_at"].isoformat(),
    }


@router.get("/session/{session_id}/file")
async def get_session_file(session_id: str):
    """
    Get the most recent file uploaded for a session.

    This is used to restore file state after browser refresh.

    Args:
        session_id: Session identifier

    Returns:
        File metadata if exists, or 404 if no file for session
    """
    db = await get_database()

    # Find the most recent file for this session
    file_doc = await db.files_collection.find_one(
        {"session_id": session_id},
        sort=[("uploaded_at", -1)]  # Most recent first
    )

    if not file_doc:
        raise HTTPException(status_code=404, detail="No file found for this session")

    return {
        "file_id": file_doc["file_id"],
        "filename": file_doc["filename"],
        "file_url": file_doc["file_url"],
        "columns": file_doc["columns"],
        "row_count": file_doc["row_count"],
        "uploaded_at": file_doc["uploaded_at"].isoformat(),
    }


@router.delete("/file/{file_id}")
async def delete_file(file_id: str):
    """
    Delete an uploaded file.

    Args:
        file_id: Unique file identifier

    Returns:
        Deletion confirmation
    """
    db = await get_database()

    # Find file metadata
    file_doc = await db.files_collection.find_one({"file_id": file_id})

    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from ImageKit
    imagekit = get_imagekit_service()
    await imagekit.delete_file(file_doc["imagekit_file_id"])

    # Delete from MongoDB
    await db.files_collection.delete_one({"file_id": file_id})

    return {"message": "File deleted successfully", "file_id": file_id}
