
from io import BytesIO
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps

from src.services.document_processors.base import ExtractedContent
from src.services.ocr.ocr_service import OCRService


class PDFProcessor:
    def __init__(self) -> None:
        self.ocr_service = OCRService()

    def _extract_table_text(self, page, table) -> str:
        rows: list[str] = []

        for row in table.rows:
            cells: list[str] = []

            for cell in row.cells:
                if cell is None:
                    cells.append("")
                    continue

                cell_text = page.get_textbox(
                    pymupdf.Rect(cell)
                ).strip()

                cells.append(cell_text)

            if any(cells):
                rows.append(" | ".join(cells))

        return "\n".join(rows)

    def _extract_page_text(self, page) -> str:
        tables = page.find_tables().tables

        if not tables:
            return page.get_text("text").strip()

        table_rects = [
            pymupdf.Rect(table.bbox)
            for table in tables
        ]

        outside_blocks: list[tuple[float, str]] = []

        for block in page.get_text("blocks"):
            rect = pymupdf.Rect(block[:4])
            block_text = block[4].strip()

            if not block_text:
                continue

            overlaps_table = any(
                rect.intersects(table_rect)
                for table_rect in table_rects
            )

            if not overlaps_table:
                outside_blocks.append((rect.y0, block_text))

        table_sections: list[tuple[float, str]] = []

        for table in tables:
            table_text = self._extract_table_text(page, table)

            if table_text:
                table_sections.append(
                    (table.bbox[1], table_text)
                )

        sections = outside_blocks + table_sections
        sections.sort(key=lambda section: section[0])

        return "\n\n".join(
            text for _, text in sections
        ).strip()

    @staticmethod
    def _normalize_text(text: str) -> str:
        return " ".join(text.casefold().split())

    def _extract_embedded_image_text(
        self,
        document,
        page,
        existing_text: str,
    ) -> list[str]:
        image_texts: list[str] = []
        seen_xrefs: set[int] = set()
        existing_normalized = self._normalize_text(
            existing_text
        )

        for image_info in page.get_images(full=True):
            xref = image_info[0]

            if xref == 0 or xref in seen_xrefs:
                continue

            seen_xrefs.add(xref)

            try:
                image_data = document.extract_image(xref)

                if not image_data:
                    continue

                image_bytes = image_data.get("image")

                if not image_bytes:
                    continue

                with Image.open(
                    BytesIO(image_bytes)
                ) as source_image:
                    image = ImageOps.exif_transpose(
                        source_image
                    ).convert("RGB")

                # Ignore very small images such as icons and logos.
                if image.width < 100 or image.height < 40:
                    continue

                extracted_text = (
                    self.ocr_service
                    .extract_text(image)
                    .strip()
                )

                if len(extracted_text) < 10:
                    continue

                normalized_image_text = (
                    self._normalize_text(extracted_text)
                )

                if not normalized_image_text:
                    continue

                # Avoid adding image text that already exists
                # in the selectable page text.
                if normalized_image_text in existing_normalized:
                    continue

                # Avoid adding a complete OCR copy of the
                # existing text when the image contains it too.
                if (
                    existing_normalized
                    and existing_normalized in normalized_image_text
                ):
                    continue

                image_texts.append(extracted_text)

            except Exception as exc:
                print(
                    "Warning: Could not OCR an embedded "
                    f"PDF image (xref={xref}): {exc}"
                )

        return image_texts

    def extract(
        self,
        file_path: str | Path,
    ) -> list[ExtractedContent]:
        path = Path(file_path)
        results: list[ExtractedContent] = []

        with pymupdf.open(path) as document:
            for page_index, page in enumerate(document):
                text = self._extract_page_text(page)

                # If the page has little or no selectable text,
                # OCR the rendered page. This supports scanned PDFs.
                if len(text) < 20:
                    pixmap = page.get_pixmap(
                        matrix=pymupdf.Matrix(2, 2),
                        alpha=False,
                    )

                    image = Image.frombytes(
                        "RGB",
                        [pixmap.width, pixmap.height],
                        pixmap.samples,
                    )

                    ocr_text = (
                        self.ocr_service
                        .extract_text(image)
                        .strip()
                    )

                    if len(ocr_text) > len(text):
                        text = ocr_text

                else:
                    # The page already has selectable text.
                    # OCR its embedded images to find additional text.
                    image_texts = (
                        self._extract_embedded_image_text(
                            document=document,
                            page=page,
                            existing_text=text,
                        )
                    )

                    if image_texts:
                        text = "\n\n".join(
                            [text, *image_texts]
                        )

                if text:
                    results.append(
                        ExtractedContent(
                            text=text,
                            source=path.name,
                            page_number=page_index + 1,
                        )
                    )

        return results
