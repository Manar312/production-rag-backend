import asyncio
from types import SimpleNamespace

import pytest

from src.services import query_service as query_module


class FakeEmbeddingService:
    def embed_query(self, question):
        return [0.1, 0.2, 0.3]


class FakeVectorStore:
    def __init__(self, matches=None, error=None):
        self.matches = matches if matches is not None else []
        self.error = error
        self.closed = False

    def search(self, **kwargs):
        if self.error:
            raise self.error
        return self.matches

    def close(self):
        self.closed = True


def make_settings(
    api_key="",
    base_url="",
    model="",
):
    return SimpleNamespace(
        LLM_API_KEY=api_key,
        LLM_BASE_URL=base_url,
        LLM_MODEL=model,
    )


def test_no_matches_returns_no_sources(monkeypatch):
    vector_store = FakeVectorStore()

    monkeypatch.setattr(
        query_module,
        "get_settings",
        lambda: make_settings(),
    )
    monkeypatch.setattr(
        query_module,
        "get_embedding_service",
        lambda: FakeEmbeddingService(),
    )
    monkeypatch.setattr(
        query_module,
        "VectorStoreService",
        lambda: vector_store,
    )

    result = asyncio.run(
        query_module.QueryService().answer(
            project_id="project-1",
            question="What is RAG?",
        )
    )

    assert result["sources"] == []
    assert result["generation_used"] is False
    assert result["project_id"] == "project-1"
    assert vector_store.closed is True


def test_matches_without_llm_return_retrieved_text(monkeypatch):
    vector_store = FakeVectorStore(
        matches=[
            {
                "asset_id": "asset-1",
                "source": "guide.pdf",
                "page_number": 2,
                "chunk_index": 0,
                "score": 0.9,
                "text": "RAG combines retrieval with generation.",
            }
        ]
    )

    monkeypatch.setattr(
        query_module,
        "get_settings",
        lambda: make_settings(),
    )
    monkeypatch.setattr(
        query_module,
        "get_embedding_service",
        lambda: FakeEmbeddingService(),
    )
    monkeypatch.setattr(
        query_module,
        "VectorStoreService",
        lambda: vector_store,
    )

    result = asyncio.run(
        query_module.QueryService().answer(
            project_id="project-1",
            question="What is RAG?",
        )
    )

    assert len(result["sources"]) == 1
    assert result["sources"][0]["source"] == "guide.pdf"
    assert "RAG combines retrieval with generation." in result["answer"]
    assert result["generation_used"] is False
    assert vector_store.closed is True


def test_vector_store_closes_when_search_fails(monkeypatch):
    vector_store = FakeVectorStore(
        error=RuntimeError("Simulated search failure")
    )

    monkeypatch.setattr(
        query_module,
        "get_settings",
        lambda: make_settings(),
    )
    monkeypatch.setattr(
        query_module,
        "get_embedding_service",
        lambda: FakeEmbeddingService(),
    )
    monkeypatch.setattr(
        query_module,
        "VectorStoreService",
        lambda: vector_store,
    )

    with pytest.raises(RuntimeError, match="Simulated search failure"):
        asyncio.run(
            query_module.QueryService().answer(
                project_id="project-1",
                question="What is RAG?",
            )
        )

    assert vector_store.closed is True
