import asyncio
import hashlib
import logging

from bson import ObjectId
from pymongo import AsyncMongoClient

from src.core.celery_app import celery_app
from src.core.config import get_settings
from src.repositories.asset_repository import AssetRepository
from src.repositories.document_content_repository import DocumentContentRepository
from src.services.chunking_service import ChunkingService
from src.services.document_processing_service import DocumentProcessingService
from src.services.embedding_service import get_embedding_service
from src.services.storage_service import StorageService
from src.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


async def _process_asset(asset_id: str) -> dict:
    if not ObjectId.is_valid(asset_id):
        raise ValueError("Invalid asset ID.")

    settings = get_settings()
    client = AsyncMongoClient(
        host="127.0.0.1",
        port=27017,
        username=settings.MONGO_APP_USERNAME,
        password=settings.MONGO_APP_PASSWORD,
        authSource=settings.MONGO_APP_AUTH_DATABASE,
        serverSelectionTimeoutMS=5000,
    )

    try:
        database = client[settings.MONGO_DATABASE]
        asset_repository = AssetRepository(database)
        content_repository = DocumentContentRepository(database)
        storage_service = StorageService()
        processing_service = DocumentProcessingService()
        chunking_service = ChunkingService()

        asset = await asset_repository.get_asset_by_id(asset_id)
        if asset is None:
            raise ValueError("Asset not found.")

        await asset_repository.update_asset_status(asset_id, "processing")

        file_path = storage_service.resolve_storage_path(asset["storage_path"])
        if not file_path.is_file():
            raise FileNotFoundError("Stored asset file was not found.")

        extracted_contents = processing_service.process_file(file_path)
        if not extracted_contents:
            raise ValueError("No content was extracted from the asset.")

        chunks = chunking_service.split_contents(extracted_contents)
        if not chunks:
            raise ValueError("No text chunks were generated from the asset.")

        content_documents = []
        for chunk_index, chunk in enumerate(chunks):
            key_source = f"{asset_id}:{chunk_index}"
            chunk_key = hashlib.sha256(key_source.encode("utf-8")).hexdigest()
            content_documents.append({
                "chunk_key": chunk_key,
                "asset_id": ObjectId(asset_id),
                "project_id": asset["project_id"],
                "text": chunk.text,
                "source": chunk.source,
                "page_number": chunk.page_number,
                "sheet_name": chunk.sheet_name,
                "slide_number": chunk.slide_number,
                "chunk_index": chunk_index,
            })

        # Idempotent Mongo upsert, then idempotent Qdrant upsert.
        await content_repository.create_many(content_documents)

        embedding_service = get_embedding_service()
        vectors = embedding_service.embed_documents(
            [item["text"] for item in content_documents]
        )

        vector_store = VectorStoreService()
        try:
            vector_store.upsert_chunks(content_documents, vectors)
        finally:
            vector_store.close()

        await asset_repository.update_asset_status(asset_id, "processed")

        return {
            "asset_id": asset_id,
            "status": "processed",
            "extracted_items": len(extracted_contents),
            "chunks_processed": len(content_documents),
            "vectors_indexed": len(vectors),
        }

    except Exception as exc:
        try:
            await AssetRepository(client[settings.MONGO_DATABASE]).update_asset_status(
                asset_id,
                "failed",
                error_message=str(exc)[:500],
            )
        except Exception:
            logger.exception("Could not update asset status after processing failure.")
        logger.exception("Asset processing failed.")
        raise
    finally:
        await client.close()


@celery_app.task(
    name="src.tasks.document_tasks.process_asset",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_asset(asset_id: str) -> dict:
    return asyncio.run(_process_asset(asset_id))
