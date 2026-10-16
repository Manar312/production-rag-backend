
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from pymongo.asynchronous.database import AsyncDatabase


def get_database(request: Request) -> AsyncDatabase:
    database = getattr(request.app.state, "db", None)

    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not available.",
        )

    return database


DatabaseDependency = Annotated[
    AsyncDatabase,
    Depends(get_database),
]