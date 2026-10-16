
from pathlib import Path

from src.services.document_processors import DocumentProcessorRegistry
from src.services.document_processors.base import ExtractedContent


class DocumentProcessingService:
    def __init__(self) -> None:
        self.registry = DocumentProcessorRegistry()

    def process_file(
        self,
        file_path: str | Path,
    ) -> list[ExtractedContent]:
        path = Path(file_path)

        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path.name}")

        processor = self.registry.get_processor(path)
        return processor.extract(path)
