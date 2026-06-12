"""Supabase Storage integration for file upload/delete/URL operations.

Wraps the Supabase Python SDK to provide a clean interface for
uploading and managing files in Supabase Storage buckets.

Usage::

    from app.integrations.supabase_storage import SupabaseStorage
    storage = SupabaseStorage()
    url = await storage.upload_file(
        path="properties/{id}/image.jpg",
        file_bytes=data,
        content_type="image/jpeg",
    )
"""

from __future__ import annotations

import logging

from supabase import create_client

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SupabaseStorage:
    """Wrapper for Supabase Storage operations.

    Lazily initializes the Supabase client on first use.
    """

    def __init__(self) -> None:
        self._client = None

    @property
    def client(self):
        """Get or create the Supabase client."""
        if self._client is None:
            settings = get_settings()
            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        return self._client

    @property
    def _bucket(self) -> str:
        """Return the configured storage bucket name."""
        return get_settings().SUPABASE_STORAGE_BUCKET

    def upload_file(
        self,
        path: str,
        file_bytes: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file to Supabase Storage and return the public URL.

        Args:
            path:         Storage path within the bucket (e.g., "props/<id>/img.jpg").
            file_bytes:   Raw file content.
            content_type: MIME type of the file.

        Returns:
            The public URL of the uploaded file.
        """
        self.client.storage.from_(self._bucket).upload(
            path=path,
            file=file_bytes,
            file_options={"content-type": content_type},
        )
        return self.get_public_url(path)

    def delete_file(self, path: str) -> None:
        """Delete a file from Supabase Storage.

        Args:
            path: Storage path within the bucket.
        """
        try:
            self.client.storage.from_(self._bucket).remove([path])
        except Exception:
            logger.warning("Failed to delete file from storage: %s", path, exc_info=True)

    def get_public_url(self, path: str) -> str:
        """Generate the public URL for a file in Supabase Storage.

        Args:
            path: Storage path within the bucket.

        Returns:
            The public URL string.
        """
        return self.client.storage.from_(self._bucket).get_public_url(path)
