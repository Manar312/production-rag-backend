from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Project name cannot be empty.")

        return value


class ProjectResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(validation_alias="_id")
    name: str
    description: str | None = None
    created_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def convert_object_id_to_string(cls, value: object) -> object:
        if isinstance(value, ObjectId):
            return str(value)

        return value
