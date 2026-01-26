"""
ImageKit Service

Handles file uploads to ImageKit.io cloud storage.
"""

import base64
from io import BytesIO
from typing import BinaryIO
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

from app.config import get_settings


class ImageKitService:
    """
    ImageKit.io file storage service.

    Handles:
    - File uploads (CSV/XLSX)
    - File URL generation
    - File deletion
    """

    def __init__(self):
        settings = get_settings()

        self.imagekit = ImageKit(
            public_key=settings.imagekit_public_key,
            private_key=settings.imagekit_private_key,
            url_endpoint=settings.imagekit_url_endpoint,
        )

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        folder: str = "data-room",
    ) -> dict:
        """
        Upload a file to ImageKit.io.

        Args:
            file_content: File content as bytes
            filename: Original filename
            folder: Folder path in ImageKit

        Returns:
            Dictionary with file_id and file_url
        """
        try:
            # Encode file content to base64
            file_base64 = base64.b64encode(file_content).decode("utf-8")

            # Upload options
            options = UploadFileRequestOptions(
                folder=f"/{folder}",
                is_private_file=False,
                use_unique_file_name=True,
            )

            # Upload to ImageKit
            result = self.imagekit.upload_file(
                file=file_base64,
                file_name=filename,
                options=options,
            )

            if result.response_metadata.http_status_code != 200:
                raise Exception(f"Upload failed: {result.response_metadata.raw}")

            return {
                "file_id": result.file_id,
                "file_url": result.url,
                "name": result.name,
            }

        except Exception as e:
            print(f"❌ ImageKit upload error: {e}")
            raise

    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from ImageKit.io.

        Args:
            file_id: ImageKit file ID

        Returns:
            True if deletion successful
        """
        try:
            result = self.imagekit.delete_file(file_id)
            return result.response_metadata.http_status_code == 204
        except Exception as e:
            print(f"❌ ImageKit delete error: {e}")
            return False

    def get_file_url(self, file_path: str) -> str:
        """
        Generate a URL for accessing a file.

        Args:
            file_path: Path to the file in ImageKit

        Returns:
            Full URL to the file
        """
        settings = get_settings()
        return f"{settings.imagekit_url_endpoint}/{file_path}"


# Global ImageKit service instance
_imagekit_service: ImageKitService | None = None


def get_imagekit_service() -> ImageKitService:
    """
    Get or create ImageKit service instance.

    Returns:
        ImageKitService instance
    """
    global _imagekit_service

    if _imagekit_service is None:
        _imagekit_service = ImageKitService()

    return _imagekit_service
