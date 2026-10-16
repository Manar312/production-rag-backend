
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedContent:
    text: str
    source: str
    page_number: int | None = None
    sheet_name: str | None = None
    slide_number: int | None = None
