import asyncio

import httpx
import pytest

from src.services import query_service as query_module


class FakeVectorStore:
    def search(self, **kwargs):
        return [{
            "asset_id": "asset-1",
            "source": "guide.pdf",
            "page_number": 1,
            "chunk_index": 0,
            "score": 0.9,
            "text": "RAG combines retrieval and generation.",
        }]

    def close(self):
        pass


class FakeResponse:
    def __init__(self, status_code=200, data=None, invalid_json=False):
        self.status_code = status_code
        self.data = data
        self.invalid_json = invalid_json
        self.is_error = status_code >= 400
        self.request = httpx.Request(
            "POST", "https://example.test/chat/completions"
        )

    def raise_for_status(self):
        if self.is_error:
            response = httpx.Response(
                self.status_code, request=self.request
            )
            raise httpx.HTTPStatusError(
                "Simulated provider error",
                request=self.request,
                response=response,
            )

    def json(self):
        if self.invalid_json:
            raise ValueError("Invalid JSON")
        return self.data


class FakeAsyncClient:
    response = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, *args, **kwargs):
        return self.response


def setup_query(monkeypatch, response):
    FakeAsyncClient.response = response
    settings = type("Settings", (), {
        "LLM_API_KEY": "test-key",
        "LLM_BASE_URL": "https://example.test/v1",
        "LLM_MODEL": "test-model",
    })()

    monkeypatch.setattr(query_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        query_module,
        "get_embedding_service",
        lambda: type("Embedding", (), {
            "embed_query": lambda self, question: [0.1, 0.2, 0.3],
        })(),
    )
    monkeypatch.setattr(query_module, "VectorStoreService", FakeVectorStore)
    monkeypatch.setattr(
        query_module.httpx, "AsyncClient", FakeAsyncClient
    )


def test_valid_llm_response(monkeypatch):
    setup_query(monkeypatch, FakeResponse(data={
        "choices": [{
            "message": {"content": "RAG retrieves relevant context."}
        }]
    }))

    result = asyncio.run(query_module.QueryService().answer(
        project_id="project-1", question="What is RAG?"
    ))

    assert result["generation_used"] is True
    assert result["answer"] == "RAG retrieves relevant context."


def test_invalid_llm_json_is_rejected(monkeypatch):
    setup_query(monkeypatch, FakeResponse(invalid_json=True))

    with pytest.raises(RuntimeError, match="invalid response"):
        asyncio.run(query_module.QueryService().answer(
            project_id="project-1", question="What is RAG?"
        ))


def test_missing_llm_choices_are_rejected(monkeypatch):
    setup_query(monkeypatch, FakeResponse(data={"unexpected": "response"}))

    with pytest.raises(RuntimeError, match="invalid response"):
        asyncio.run(query_module.QueryService().answer(
            project_id="project-1", question="What is RAG?"
        ))


def test_llm_http_error_is_propagated(monkeypatch):
    setup_query(monkeypatch, FakeResponse(status_code=500))

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(query_module.QueryService().answer(
            project_id="project-1", question="What is RAG?"
        ))
