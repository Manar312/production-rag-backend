
from pathlib import Path

from src.services.document_processors.base import ExtractedContent


class TextProcessor:
    def extract(self, file_path: str | Path) -> list[ExtractedContent]:
        path = Path(file_path)

        text = None
        for encoding in ("utf-8-sig", "utf-8", "cp1256", "cp1252"):
            try:
                text = path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise ValueError(
                "Could not decode the text file using supported encodings."
            )

        text = text.strip()
        if not text:
            return []

        return [
            ExtractedContent(
                text=text,
                source=path.name,
            )
        ]
