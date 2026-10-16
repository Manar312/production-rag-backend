
from pathlib import Path

from PIL import Image, ImageOps

from src.services.document_processors.base import ExtractedContent
from src.services.ocr.ocr_service import OCRService


class ImageProcessor:
    SUPPORTED_EXTENSIONS = {
        ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"
    }

    def __init__(self) -> None:
        self.ocr_service = OCRService()

    def extract(self, file_path: str | Path) -> list[ExtractedContent]:
        path = Path(file_path)

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError("Unsupported image format.")

        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            text = self.ocr_service.extract_text(image)

        if not text.strip():
            return []

        return [
            ExtractedContent(
                text=text.strip(),
                source=path.name,
            )
        ]
