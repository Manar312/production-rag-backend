import pytest

from src.services.chunking_service import ChunkingService
from src.services.document_processors.base import ExtractedContent


def test_short_text_returns_one_chunk() -> None:
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    content = ExtractedContent(text="Short test.", source="test.txt")

    chunks = service.split_content(content)

    assert len(chunks) == 1
    assert chunks[0].text == "Short test."


def test_empty_text_returns_no_chunks() -> None:
    service = ChunkingService()
    content = ExtractedContent(text="   ", source="empty.txt")

    assert service.split_content(content) == []


def test_chunks_do_not_exceed_configured_size() -> None:
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    content = ExtractedContent(
        text=" ".join(f"word{i}" for i in range(100)),
        source="long.txt",
    )

    chunks = service.split_content(content)

    assert len(chunks) > 1
    assert all(len(chunk.text) <= 100 for chunk in chunks)


def test_overlap_is_preserved_between_adjacent_chunks() -> None:
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    content = ExtractedContent(
        text=" ".join(f"word{i}" for i in range(100)),
        source="overlap.txt",
    )

    chunks = service.split_content(content)

    assert len(chunks) > 1

    for previous, current in zip(chunks, chunks[1:]):
        assert previous.text.split()[-1] in current.text.split()


def test_arabic_text_and_metadata_are_preserved() -> None:
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    content = ExtractedContent(
        text="هذه فقرة عربية لاختبار تقسيم النص والحفاظ على السياق. " * 10,
        source="arabic.pdf",
        page_number=3,
    )

    chunks = service.split_content(content)

    assert chunks
    assert all(len(chunk.text) <= 100 for chunk in chunks)
    assert all(chunk.source == "arabic.pdf" for chunk in chunks)
    assert all(chunk.page_number == 3 for chunk in chunks)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))


def test_sheet_and_slide_metadata_are_preserved() -> None:
    service = ChunkingService(chunk_size=100, chunk_overlap=20)
    content = ExtractedContent(
        text="Spreadsheet and presentation content " * 10,
        source="report",
        sheet_name="Sales",
        slide_number=2,
    )

    chunks = service.split_content(content)

    assert chunks
    assert all(chunk.sheet_name == "Sales" for chunk in chunks)
    assert all(chunk.slide_number == 2 for chunk in chunks)


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap"),
    [
        (0, 0),
        (-1, 0),
        (100, -1),
        (100, 100),
        (100, 101),
    ],
)
def test_invalid_configuration_raises_value_error(
    chunk_size: int,
    chunk_overlap: int,
) -> None:
    with pytest.raises(ValueError):
        ChunkingService(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
