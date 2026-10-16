
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from bson import ObjectId
from fastapi import UploadFile

from src.core.config import get_settings


@dataclass
class StoredFile:
    stored_filename: str
    storage_path: str
    size_bytes: int


class StorageService:
    CHUNK_SIZE = 1024 * 1024  # 1 MB

    def __init__(self) -> None:
        self.settings = get_settings()

        # Resolve the storage directory relative to the project root.
        project_root = Path(__file__).resolve().parents[2]
        configured_path = Path(self.settings.UPLOAD_DIRECTORY)

        if configured_path.is_absolute():
            self.storage_root = configured_path
        else:
            self.storage_root = project_root / configured_path

    async def save_upload(
        self,
        upload_file: UploadFile,
        project_id: str,
    ) -> StoredFile:
        if not ObjectId.is_valid(project_id):
            raise ValueError("Invalid project ID.")

        safe_project_id = str(ObjectId(project_id))

        original_filename = upload_file.filename or ""
        extension = Path(original_filename).suffix.lower()

        if not extension:
            raise ValueError("The uploaded file must have an extension.")

        project_directory = self.storage_root / safe_project_id
        project_directory.mkdir(parents=True, exist_ok=True)

        stored_filename = f"{uuid4().hex}{extension}"
        destination = project_directory / stored_filename

        max_bytes = self.settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        total_bytes = 0

        try:
            with destination.open("wb") as output_file:
                while True:
                    chunk = await upload_file.read(self.CHUNK_SIZE)

                    if not chunk:
                        break

                    if total_bytes + len(chunk) > max_bytes:
                        raise ValueError("Uploaded file exceeds the maximum size.")

                    output_file.write(chunk)
                    total_bytes += len(chunk)

        except BaseException:
            destination.unlink(missing_ok=True)
            raise

        return StoredFile(
            stored_filename=stored_filename,
            storage_path=str(destination.relative_to(self.storage_root)),
            size_bytes=total_bytes,
        )

    def resolve_storage_path(self, storage_path: str) -> Path:
        relative_path = Path(storage_path)

        if relative_path.is_absolute():
            raise ValueError("Expected a relative storage path.")

        target = (self.storage_root / relative_path).resolve()
        root = self.storage_root.resolve()

        if not target.is_relative_to(root) or target == root:
            raise ValueError("Invalid storage path.")

        return target

    def delete_stored_file(self, storage_path: str) -> None:
        relative_path = Path(storage_path)

        if relative_path.is_absolute():
            raise ValueError("Expected a relative storage path.")

        target = (self.storage_root / relative_path).resolve()
        root = self.storage_root.resolve()

        # Ensure the target stays inside the configured storage directory.
        if not target.is_relative_to(root) or target == root:
            raise ValueError("Invalid storage path.")

        target.unlink(missing_ok=True)

        # Remove the project directory if it is empty.
        try:
            target.parent.rmdir()
        except OSError:
            pass
