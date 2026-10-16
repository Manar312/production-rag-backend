
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from datetime import datetime, timezone

class AssetRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self.collection: AsyncCollection = database["assets"]

    async def create_asset(
        self,
        asset_data: dict[str, Any],
    ) -> dict[str, Any]:
        document = dict(asset_data)

        result = await self.collection.insert_one(document)

        document["_id"] = result.inserted_id

        return document

    async def get_asset_by_id(
        self,
        asset_id: str,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(asset_id):
            return None

        return await self.collection.find_one(
            {"_id": ObjectId(asset_id)}
        )

    async def update_asset_status(
        self,
        asset_id: str,
        new_status: str,
        error_message: str | None = None,
    ) -> bool:
        if not ObjectId.is_valid(asset_id):
            return False

        update_fields: dict[str, Any] = {
            "status": new_status,
            "updated_at": datetime.now(timezone.utc),
        }

        if error_message is not None:
            update_fields["error_message"] = error_message
        elif new_status != "failed":
            update_fields["error_message"] = None

        result = await self.collection.update_one(
            {"_id": ObjectId(asset_id)},
            {"$set": update_fields},
        )

        return result.matched_count == 1



    async def get_project_assets(
        self,
        project_id: str,
    ) -> list[dict[str, Any]]:
        if not ObjectId.is_valid(project_id):
            return []

        cursor = (
            self.collection.find(
                {"project_id": ObjectId(project_id)}
            )
            .sort("created_at", -1)
        )

        return await cursor.to_list(length=100)
