from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

from src.services.document_processing_service import (
    DocumentProcessingService,
)


def create_text_image(path: Path, text: str) -> None:
    image = Image.new("RGB", (1200, 300), "white")
    draw = ImageDraw.Draw(image)

    font_path = Path(r"C:\Windows\Fonts\arial.ttf")
    if font_path.is_file():
        font = ImageFont.truetype(str(font_path), 48)
    else:
        font = ImageFont.load_default()

    draw.text((40, 100), text, fill="black", font=font)
    image.save(path)


def create_digital_pdf(path: Path) -> None:
    document = pymupdf.open()
    page = document.new_page()

    page.insert_text(
        (50, 80),
        "This is selectable digital PDF text for testing.",
        fontsize=14,
    )

    document.save(path)
    document.close()


def create_mixed_pdf(pdf_path: Path, image_path: Path) -> None:
    create_text_image(image_path, "Hidden Image Text 98765")

    document = pymupdf.open()
    page = document.new_page(width=595, height=842)

    page.insert_text(
        (50, 80),
        "This is selectable PDF text with enough characters.",
        fontsize=14,
    )

    page.insert_image(
        pymupdf.Rect(40, 180, 555, 420),
        filename=str(image_path),
    )

    document.save(pdf_path)
    document.close()


def create_scanned_pdf(pdf_path: Path, image_path: Path) -> None:
    create_text_image(image_path, "Scanned RAG Document Test 12345")

    document = pymupdf.open()
    page = document.new_page(width=595, height=842)

    page.insert_image(
        pymupdf.Rect(40, 180, 555, 420),
        filename=str(image_path),
    )

    document.save(pdf_path)
    document.close()


def test_extracts_selectable_pdf_text(tmp_path: Path) -> None:
    pdf_path = tmp_path / "digital.pdf"
    create_digital_pdf(pdf_path)

    results = DocumentProcessingService().process_file(pdf_path)
    combined_text = "\n".join(item.text for item in results)

    assert results
    assert "selectable digital PDF text" in combined_text
    assert results[0].page_number == 1


def test_extracts_text_from_mixed_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "mixed.pdf"
    image_path = tmp_path / "mixed.png"
    create_mixed_pdf(pdf_path, image_path)

    results = DocumentProcessingService().process_file(pdf_path)
    combined_text = "\n".join(item.text for item in results)

    assert results
    assert "selectable PDF text" in combined_text
    assert "Hidden Image Text" in combined_text


def test_extracts_text_from_scanned_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "scanned.pdf"
    image_path = tmp_path / "scanned.png"
    create_scanned_pdf(pdf_path, image_path)

    results = DocumentProcessingService().process_file(pdf_path)
    combined_text = "\n".join(item.text for item in results)

    assert results
    assert "Scanned RAG Document Test" in combined_text
    assert results[0].page_number == 1
