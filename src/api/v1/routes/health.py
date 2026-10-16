
from fastapi import APIRouter

from src.db.dependencies import DatabaseDependency


router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "rag-api",
    }


@router.get("/health/database")
async def database_health(database: DatabaseDependency):
    await database.command("ping")

    return {
        "status": "ok",
        "database": "connected",
    }
