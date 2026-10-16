
from typing import Any

from bson import ObjectId
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase


class ProjectRepository:
    def __init__(self, database: AsyncDatabase) -> None:
        self.collection: AsyncCollection = database["projects"]

    async def create_project(
        self,
        project_data: dict[str, Any],
    ) -> dict[str, Any]:
        document = dict(project_data)

        result = await self.collection.insert_one(document)

        document["_id"] = result.inserted_id

        return document

    async def get_project_by_id(
        self,
        project_id: str,
    ) -> dict[str, Any] | None:
        if not ObjectId.is_valid(project_id):
            return None

        return await self.collection.find_one(
            {"_id": ObjectId(project_id)}
        )
