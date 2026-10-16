
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.db.dependencies import DatabaseDependency
from src.repositories.asset_repository import AssetRepository
from src.repositories.project_repository import ProjectRepository
from src.schemas.asset import AssetResponse
from src.services.asset_service import AssetService
from src.services.storage_service import StorageService


router = APIRouter(
    prefix="/api/v1/projects/{project_id}/assets",
    tags=["Assets"],
)


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
)

async def upload_asset(
    project_id: str,
    database: DatabaseDependency,
    upload_file: UploadFile = File(...),
) -> AssetResponse:
    asset_repository = AssetRepository(database)
    project_repository = ProjectRepository(database)
    storage_service = StorageService()

    service = AssetService(
        asset_repository=asset_repository,
        project_repository=project_repository,
        storage_service=storage_service,
    )

    try:
        return await service.upload_asset(
            project_id=project_id,
            upload_file=upload_file,
        )
    except ValueError as exc:
        if str(exc) == "Project not found.":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    finally:
        await upload_file.close()
