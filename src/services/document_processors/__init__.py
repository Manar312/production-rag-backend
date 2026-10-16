
from pathlib import Path
from typing import Protocol

from src.services.document_processors.base import ExtractedContent
from src.services.document_processors.docx_processor import DOCXProcessor
from src.services.document_processors.image_processor import ImageProcessor
from src.services.document_processors.pdf_processor import PDFProcessor
from src.services.document_processors.pptx_processor import PPTXProcessor
from src.services.document_processors.spreadsheet_processor import (
    SpreadsheetProcessor,
)
from src.services.document_processors.text_processor import TextProcessor


class DocumentProcessor(Protocol):
    def extract(self, file_path: str | Path) -> list[ExtractedContent]:
        ...


class DocumentProcessorRegistry:
    def __init__(self) -> None:
        self._processors = {
            ".pdf": PDFProcessor(),
            ".png": ImageProcessor(),
            ".jpg": ImageProcessor(),
            ".jpeg": ImageProcessor(),
            ".tif": ImageProcessor(),
            ".tiff": ImageProcessor(),
            ".bmp": ImageProcessor(),
            ".webp": ImageProcessor(),
            ".docx": DOCXProcessor(),
            ".txt": TextProcessor(),
            ".csv": SpreadsheetProcessor(),
            ".xlsx": SpreadsheetProcessor(),
            ".pptx": PPTXProcessor(),
        }

    def get_processor(self, file_path: str | Path) -> DocumentProcessor:
        extension = Path(file_path).suffix.lower()
        processor = self._processors.get(extension)

        if processor is None:
            raise ValueError(
                f"No document processor is registered for '{extension}'."
            )

        return processor
