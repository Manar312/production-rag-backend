from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models

from src.core.config import get_settings


class VectorStoreService:
    def __init__(self) -> None:
        settings = get_settings()
        self.collection_name = settings.QDRANT_COLLECTION
        self.vector_size = settings.EMBEDDING_DIMENSION
        self.client = QdrantClient(url=settings.QDRANT_URL)

    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            info = self.client.get_collection(self.collection_name)
            actual = info.config.params.vectors
            actual_size = actual.size if hasattr(actual, "size") else None

            if actual_size != self.vector_size:
                raise ValueError(
                    f"Collection vector size is {actual_size}; "
                    f"expected {self.vector_size}. Collection was not changed."
                )
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.vector_size,
                distance=models.Distance.COSINE,
            ),
        )

        # Payload index accelerates project-scoped retrieval.
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="project_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
            wait=True,
        )

    def upsert_chunks(
        self,
        chunks: list[dict],
        vectors: list[list[float]],
    ) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunks and vectors counts do not match.")
        if not chunks:
            return

        self.ensure_collection()
        points = []

        for chunk, vector in zip(chunks, vectors):
            points.append(
                models.PointStruct(
                    id=str(uuid5(NAMESPACE_URL, chunk["chunk_key"])),
                    vector=vector,
                    payload={
                        "chunk_key": chunk["chunk_key"],
                        "asset_id": str(chunk["asset_id"]),
                        "project_id": str(chunk["project_id"]),
                        "text": chunk["text"],
                        "source": chunk["source"],
                        "page_number": chunk.get("page_number"),
                        "sheet_name": chunk.get("sheet_name"),
                        "slide_number": chunk.get("slide_number"),
                        "chunk_index": chunk["chunk_index"],
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

    def search(
        self,
        query_vector: list[float],
        project_id: str,
        limit: int = 5,
    ) -> list[dict]:
        self.ensure_collection()
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="project_id",
                        match=models.MatchValue(value=project_id),
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
        )

        matches = []
        for point in response.points:
            payload = point.payload or {}
            matches.append({**payload, "score": point.score})
        return matches

    def close(self) -> None:
        self.client.close()
