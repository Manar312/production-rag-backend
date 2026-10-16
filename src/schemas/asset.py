
from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AssetResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(validation_alias="_id")
    project_id: str
    original_filename: str
    content_type: str
    size_bytes: int = Field(ge=0)
    status: str
    created_at: datetime

    @field_validator("id", "project_id", mode="before")
    @classmethod
    def convert_object_id_to_string(cls, value: object) -> object:
        if isinstance(value, ObjectId):
            return str(value)
        return value
