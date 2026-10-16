
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import UpdateOne
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase


class DocumentContentRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self.collection: AsyncCollection = database["document_contents"]

    async def ensure_chunk_key_index(self) -> None:
        await self.collection.create_index(
            [("chunk_key", 1)],
            name="unique_chunk_key",
            unique=True,
            partialFilterExpression={
                "chunk_key": {"$type": "string"},
            },
        )

    async def create_many(
        self,
        contents: list[dict[str, Any]],
    ) -> int:
        if not contents:
            return 0

        now = datetime.now(timezone.utc)
        operations = []
        batch_keys: set[str] = set()

        for content in contents:
            document = dict(content)
            chunk_key = document.get("chunk_key")

            if not isinstance(chunk_key, str) or not chunk_key:
                raise ValueError(
                    "Every document must have a non-empty chunk_key."
                )

            if chunk_key in batch_keys:
                raise ValueError(
                    f"Duplicate chunk_key in batch: {chunk_key}"
                )

            batch_keys.add(chunk_key)

            document.pop("_id", None)
            document.pop("created_at", None)

            operations.append(
                UpdateOne(
                    {"chunk_key": chunk_key},
                    {
                        "$set": {
                            **document,
                            "updated_at": now,
                        },
                        "$setOnInsert": {
                            "created_at": now,
                        },
                    },
                    upsert=True,
                )
            )

        await self.ensure_chunk_key_index()

        result = await self.collection.bulk_write(
            operations,
            ordered=True,
        )

        return result.upserted_count + result.modified_count

    async def get_asset_contents(
        self,
        asset_id: str,
    ) -> list[dict[str, Any]]:
        if not ObjectId.is_valid(asset_id):
            return []

        cursor = (
            self.collection.find(
                {"asset_id": ObjectId(asset_id)}
            )
            .sort(
                [
                    ("page_number", 1),
                    ("chunk_index", 1),
                ]
            )
        )

        return await cursor.to_list(length=1000)
