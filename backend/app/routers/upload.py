"""
File Upload Router

Handles CSV/XLSX file uploads to ImageKit and stores metadata in MongoDB.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.models.schemas import FileUploadResponse

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="CSV or XLSX file to upload"),
    session_id: str = Form(..., description="Session identifier"),
):
    """
    Upload a CSV or XLSX file for analysis.

    - Validates file type and size (max 10MB)
    - Uploads to ImageKit.io for storage
    - Extracts column names and row count
    - Stores metadata in MongoDB

    Returns file metadata including URL and schema information.
    """
    # TODO: Implement in feature/05-file-upload
    raise HTTPException(
        status_code=501,
        detail="File upload not yet implemented. Coming in feature/05-file-upload",
    )
