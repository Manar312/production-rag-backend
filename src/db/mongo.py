
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from src.core.config import get_settings


class MongoDB:
    def __init__(self) -> None:
        self.client: AsyncMongoClient | None = None
        self.database: AsyncDatabase | None = None

    async def connect(self) -> None:
        settings = get_settings()

        username = settings.MONGO_APP_USERNAME
        password = settings.MONGO_APP_PASSWORD
        auth_database = settings.MONGO_APP_AUTH_DATABASE

        self.client = AsyncMongoClient(
            host="127.0.0.1",
            port=27017,
            username=username,
            password=password,
            authSource=auth_database,
            serverSelectionTimeoutMS=5000,
        )

        self.database = self.client[settings.MONGO_DATABASE]

        await self.client.admin.command("ping")

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close()
            self.client = None
            self.database = None