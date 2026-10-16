from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Question must not be empty.")

        return value


class SourceItem(BaseModel):
    asset_id: str
    source: str
    page_number: int | None = None
    sheet_name: str | None = None
    slide_number: int | None = None
    chunk_index: int
    score: float
    text: str


class QueryResponse(BaseModel):
    project_id: str
    question: str
    answer: str
    generation_used: bool
    sources: list[SourceItem]
