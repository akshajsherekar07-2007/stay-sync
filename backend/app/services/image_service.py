"""Image service — business logic for property image management.

Handles image upload to Supabase Storage, metadata persistence,
reordering, primary image management, and deletion.
Enforces 5MB size limit and 20-images-per-property cap.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.integrations.supabase_storage import SupabaseStorage
from app.repositories.image_repository import ImageRepository
from app.repositories.property_repository import PropertyRepository
from app.schemas.image import ImageReorder, ImageUpdate


MAX_IMAGES_PER_PROPERTY = 20


class ImageService:
    """Orchestrates image upload, deletion, and management.

    Args:
        image_repo:    Repository for property_images table.
        property_repo: Repository for properties table.
        storage:       Supabase Storage integration.
    """

    def __init__(
        self,
        image_repo: ImageRepository,
        property_repo: PropertyRepository,
        storage: SupabaseStorage,
    ) -> None:
        self._image_repo = image_repo
        self._property_repo = property_repo
        self._storage = storage

    async def upload_image(
        self,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        db: AsyncSession,
    ):
        """Upload an image file and create the metadata record.

        Validates:
        - Property ownership
        - MIME type is allowed
        - File size ≤ 5MB
        - Image count ≤ 20 per property

        Returns the created PropertyImage instance.
        """
        # Ownership check
        await self._verify_property_ownership(property_id, owner_id)

        settings = get_settings()

        # Validate MIME type
        allowed_mimes = [m.strip() for m in settings.ALLOWED_IMAGE_MIMES.split(",")]
        if content_type not in allowed_mimes:
            raise BadRequestException(
                message=f"Invalid image type. Allowed: {', '.join(allowed_mimes)}",
                code="INVALID_IMAGE_TYPE",
            )

        # Validate file size
        if len(file_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
            raise BadRequestException(
                message=f"Image size exceeds {settings.MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB limit.",
                code="IMAGE_TOO_LARGE",
            )

        # Check image count
        current_count = await self._image_repo.count_by_property(property_id)
        if current_count >= MAX_IMAGES_PER_PROPERTY:
            raise BadRequestException(
                message=f"Maximum {MAX_IMAGES_PER_PROPERTY} images per property.",
                code="IMAGE_LIMIT_REACHED",
            )

        # Build storage path
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
        image_id = uuid.uuid4()
        storage_path = f"properties/{property_id}/{image_id}.{ext}"

        # Upload to Supabase Storage
        url = self._storage.upload_file(
            path=storage_path,
            file_bytes=file_bytes,
            content_type=content_type,
        )

        # Set as primary if it's the first image
        is_primary = current_count == 0

        # Create DB record
        image = await self._image_repo.create(
            id=image_id,
            entity_type=entity_type,
            entity_id=entity_id,
            property_id=property_id,
            url=url,
            storage_path=storage_path,
            file_size_bytes=len(file_bytes),
            mime_type=content_type,
            is_primary=is_primary,
            sort_order=current_count,
        )
        await db.commit()
        await db.refresh(image)
        return image

    async def delete_image(
        self,
        image_id: uuid.UUID,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """Soft-delete an image and remove from storage."""
        await self._verify_property_ownership(property_id, owner_id)

        image = await self._image_repo.get(image_id)
        if image is None or image.property_id != property_id:
            raise NotFoundException(
                message="Image not found.",
                code="IMAGE_NOT_FOUND",
            )

        # Soft delete in DB
        await self._image_repo.soft_delete(image_id)

        # Delete from Supabase Storage
        self._storage.delete_file(image.storage_path)

        await db.commit()

    async def update_image(
        self,
        image_id: uuid.UUID,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: ImageUpdate,
        db: AsyncSession,
    ):
        """Update image metadata (alt_text, is_primary).

        Returns the updated image.
        """
        await self._verify_property_ownership(property_id, owner_id)

        image = await self._image_repo.get(image_id)
        if image is None or image.property_id != property_id:
            raise NotFoundException(
                message="Image not found.",
                code="IMAGE_NOT_FOUND",
            )

        if data.is_primary is True:
            await self._image_repo.set_primary(image_id, property_id)

        if data.alt_text is not None:
            from sqlalchemy import update as sa_update
            from app.models.property_image import PropertyImage

            await db.execute(
                sa_update(PropertyImage)
                .where(PropertyImage.id == image_id)
                .values(alt_text=data.alt_text)
            )

        await db.commit()
        # Refresh
        image = await self._image_repo.get(image_id)
        return image

    async def reorder_images(
        self,
        property_id: uuid.UUID,
        owner_id: uuid.UUID,
        data: ImageReorder,
        db: AsyncSession,
    ) -> None:
        """Batch update sort_order for images."""
        await self._verify_property_ownership(property_id, owner_id)

        reorder_items = [
            {"id": item.id, "sort_order": item.sort_order}
            for item in data.images
        ]
        await self._image_repo.update_sort_orders(reorder_items)
        await db.commit()

    async def list_images(self, property_id: uuid.UUID):
        """List all images for a property."""
        return await self._image_repo.list_by_property(property_id)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _verify_property_ownership(
        self, property_id: uuid.UUID, owner_id: uuid.UUID
    ) -> None:
        """Verify that the user owns the property."""
        prop = await self._property_repo.get(property_id)
        if prop is None or prop.is_deleted:
            raise NotFoundException(
                message="Property not found.",
                code="PROPERTY_NOT_FOUND",
            )
        if prop.owner_id != owner_id:
            raise ForbiddenException(
                message="You do not own this property.",
                code="NOT_PROPERTY_OWNER",
            )
