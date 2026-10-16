
import asyncio

from src.db.mongo import MongoDB


async def main() -> None:
    mongo = MongoDB()

    try:
        await mongo.connect()

        result = await mongo.database.command("ping")
        print("MongoDB connection: SUCCESS")
        print("Ping result:", result["ok"])

    finally:
        await mongo.close()


if __name__ == "__main__":
    asyncio.run(main())