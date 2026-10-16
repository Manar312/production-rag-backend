from datetime import datetime, timezone

from src.repositories.project_repository import ProjectRepository
from src.schemas.project import ProjectCreate, ProjectResponse


class ProjectService:
    def __init__(self, repository: ProjectRepository) -> None:
        self.repository = repository

    async def create_project(
        self,
        project_data: ProjectCreate,
    ) -> ProjectResponse:
        document = project_data.model_dump()
        document["created_at"] = datetime.now(timezone.utc)

        saved_project = await self.repository.create_project(document)

        return ProjectResponse.model_validate(saved_project)
