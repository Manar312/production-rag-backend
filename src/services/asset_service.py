
from datetime import datetime, timezone
from pathlib import Path
import logging

from fastapi import UploadFile

from src.core.celery_app import celery_app
from src.core.config import get_settings
from src.repositories.asset_repository import AssetRepository
from src.repositories.project_repository import ProjectRepository
from src.schemas.asset import AssetResponse
from src.services.storage_service import StorageService


logger = logging.getLogger(__name__)


class AssetService:
    def __init__(
        self,
        asset_repository: AssetRepository,
        project_repository: ProjectRepository,
        storage_service: StorageService,
    ) -> None:
        self.asset_repository = asset_repository
        self.project_repository = project_repository
        self.storage_service = storage_service
        self.settings = get_settings()

    async def upload_asset(
        self,
        project_id: str,
        upload_file: UploadFile,
    ) -> AssetResponse:
        if not upload_file.filename:
            raise ValueError("A filename is required.")

        original_filename = (
            upload_file.filename.replace("\\", "/").rsplit("/", 1)[-1]
        )
        extension = Path(original_filename).suffix.lower()

        if not extension:
            raise ValueError("The uploaded file must have an extension.")

        if extension not in self.settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise ValueError("This file extension is not allowed.")

        project = await self.project_repository.get_project_by_id(
            project_id
        )

        if project is None:
            raise ValueError("Project not found.")

        stored_file = await self.storage_service.save_upload(
            upload_file=upload_file,
            project_id=project_id,
        )

        asset_data = {
            "project_id": project["_id"],
            "original_filename": original_filename,
            "stored_filename": stored_file.stored_filename,
            "storage_path": stored_file.storage_path,
            "content_type": (
                upload_file.content_type or "application/octet-stream"
            ),
            "size_bytes": stored_file.size_bytes,
            "status": "uploaded",
            "created_at": datetime.now(timezone.utc),
        }

        try:
            saved_asset = await self.asset_repository.create_asset(
                asset_data
            )
        except Exception:
            try:
                self.storage_service.delete_stored_file(
                    stored_file.storage_path
                )
            except Exception:
                logger.exception(
                    "Failed to clean up stored file after asset "
                    "creation failed."
                )
            raise

        asset_id = str(saved_asset["_id"])

        # Record that the asset is waiting for background processing.
        updated = await self.asset_repository.update_asset_status(
            asset_id,
            "queued",
        )

        if not updated:
            raise RuntimeError(
                "Asset was saved but its status could not be updated."
            )

        saved_asset["status"] = "queued"

        try:
            celery_app.send_task(
                "src.tasks.document_tasks.process_asset",
                args=[asset_id],
            )
        except Exception as exc:
            logger.exception(
                "Failed to enqueue asset processing task."
            )

            await self.asset_repository.update_asset_status(
                asset_id,
                "failed",
                error_message=f"Failed to enqueue task: {str(exc)[:400]}",
            )

            raise RuntimeError(
                "Asset was saved, but background processing "
                "could not be queued."
            ) from exc

        return AssetResponse.model_validate(saved_asset)
