from dataclasses import dataclass

from src.services.document_processors.base import ExtractedContent


@dataclass(frozen=True)
class TextChunk:
    text: str
    source: str
    page_number: int | None = None
    sheet_name: str | None = None
    slide_number: int | None = None
    chunk_index: int = 0


class ChunkingService:
    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 200,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ("\n\n", "\n", ". ", "! ", "? ", "؟ ", " ")

    def _find_chunk_end(self, text: str, start: int) -> int:
        hard_end = min(start + self.chunk_size, len(text))

        if hard_end == len(text):
            return hard_end

        # Prefer a natural boundary in the latter part of the chunk.
        minimum_end = start + int(self.chunk_size * 0.6)
        search_text = text[minimum_end:hard_end]

        best_end = -1

        for separator in self.separators:
            position = search_text.rfind(separator)

            if position >= 0:
                candidate_end = minimum_end + position + len(separator)

                if candidate_end > best_end:
                    best_end = candidate_end

        return best_end if best_end > start else hard_end

    def _find_next_start(self, text: str, end: int) -> int:
        target_start = max(end - self.chunk_overlap, 0)

        if target_start == 0 or target_start >= len(text):
            return target_start

        # Avoid starting in the middle of a word when possible.
        if not text[target_start - 1].isspace() and not text[target_start].isspace():
            next_space = text.find(" ", target_start)

            if next_space != -1 and next_space < end:
                target_start = next_space + 1

        return target_start

    def split_content(
        self,
        content: ExtractedContent,
    ) -> list[TextChunk]:
        text = content.text.strip()

        if not text:
            return []

        chunks: list[TextChunk] = []
        start = 0

        while start < len(text):
            end = self._find_chunk_end(text, start)
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        source=content.source,
                        page_number=content.page_number,
                        sheet_name=content.sheet_name,
                        slide_number=content.slide_number,
                        chunk_index=len(chunks),
                    )
                )

            if end >= len(text):
                break

            next_start = self._find_next_start(text, end)

            # Safety guard: always make progress.
            if next_start <= start:
                next_start = end

            start = next_start

        return chunks

    def split_contents(
        self,
        contents: list[ExtractedContent],
    ) -> list[TextChunk]:
        chunks: list[TextChunk] = []

        for content in contents:
            chunks.extend(self.split_content(content))

        return chunks
