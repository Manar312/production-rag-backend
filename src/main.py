from contextlib import asynccontextmanager
from src.api.v1.routes.assets import router as assets_router
from fastapi import FastAPI

from src.api.v1.routes.health import router as health_router
from src.api.v1.routes.projects import router as projects_router
from src.api.v1.routes.query import router as query_router
from src.db.mongo import MongoDB


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongo = MongoDB()

    try:
        await mongo.connect()

        app.state.mongo = mongo
        app.state.db = mongo.database

        yield

    finally:
        await mongo.close()


app = FastAPI(
    title="Production RAG API",
    description="Backend API for a document-based RAG system.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(assets_router)
app.include_router(query_router)
