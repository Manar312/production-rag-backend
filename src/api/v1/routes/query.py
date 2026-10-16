import logging

import httpx
from fastapi import APIRouter, HTTPException, status

from src.db.dependencies import DatabaseDependency
from src.repositories.project_repository import ProjectRepository
from src.schemas.query import QueryRequest, QueryResponse
from src.services.query_service import QueryService

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/projects/{project_id}/query",
    tags=["RAG Query"],
)


@router.post("", response_model=QueryResponse)
async def query_project(
    project_id: str,
    request: QueryRequest,
    database: DatabaseDependency,
) -> QueryResponse:
    project = await ProjectRepository(database).get_project_by_id(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    try:
        result = await QueryService().answer(
            project_id=project_id,
            question=request.question,
            top_k=request.top_k,
        )
        return QueryResponse.model_validate(result)

    except httpx.HTTPError as exc:
        logger.exception("LLM provider request failed.")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The answer generation provider is temporarily unavailable.",
        ) from exc

    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
