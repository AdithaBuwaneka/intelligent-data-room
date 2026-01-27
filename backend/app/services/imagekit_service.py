"""
ImageKit Service

Handles file uploads to ImageKit.io cloud storage.
"""

import asyncio
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from imagekitio import ImageKit

from app.config import get_settings

# Thread pool for running sync ImageKit operations
_executor = ThreadPoolExecutor(max_workers=3)


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

        # New ImageKit SDK API (v5.x)
        self.imagekit = ImageKit(
            private_key=settings.imagekit_private_key,
        )
        self.url_endpoint = settings.imagekit_url_endpoint

    def _upload_sync(self, file_content: bytes, filename: str, folder: str) -> dict:
        """Synchronous upload to ImageKit."""
        result = self.imagekit.files.upload(
            file=BytesIO(file_content),
            file_name=filename,
            folder=f"/{folder}",
        )

        return {
            "file_id": result.file_id,
            "file_url": result.url,
            "name": result.name,
        }

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
            # Run sync upload in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                _executor,
                self._upload_sync,
                file_content,
                filename,
                folder,
            )

            return result

        except Exception as e:
            print(f"❌ ImageKit upload error: {e}")
            raise

    def _delete_sync(self, file_id: str) -> bool:
        """Synchronous delete from ImageKit."""
        self.imagekit.files.delete(file_id=file_id)
        return True

    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from ImageKit.io.

        Args:
            file_id: ImageKit file ID

        Returns:
            True if deletion successful
        """
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                _executor,
                self._delete_sync,
                file_id,
            )
            return True
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
        return f"{self.url_endpoint}/{file_path}"


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
