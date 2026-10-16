from fastapi import APIRouter, status

from src.db.dependencies import DatabaseDependency
from src.repositories.project_repository import ProjectRepository
from src.schemas.project import ProjectCreate, ProjectResponse
from src.services.project_service import ProjectService


router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Projects"],
)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project_data: ProjectCreate,
    database: DatabaseDependency,
) -> ProjectResponse:
    repository = ProjectRepository(database)
    service = ProjectService(repository)

    return await service.create_project(project_data)
