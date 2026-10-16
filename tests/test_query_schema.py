from pydantic import ValidationError

from src.schemas.query import QueryRequest


def test_question_is_trimmed():
    request = QueryRequest(question="  What is RAG?  ")

    assert request.question == "What is RAG?"


def test_arabic_question_is_preserved():
    question = "\u0645\u0627 \u0647\u0648 RAG\u061f"

    request = QueryRequest(question=question)

    assert request.question == question


def test_whitespace_only_question_is_rejected():
    try:
        QueryRequest(question="   ")
    except ValidationError:
        return

    raise AssertionError("Whitespace-only questions must be rejected.")


def test_top_k_defaults_to_five():
    request = QueryRequest(question="What is RAG?")

    assert request.top_k == 5


def test_top_k_below_minimum_is_rejected():
    try:
        QueryRequest(question="What is RAG?", top_k=0)
    except ValidationError:
        return

    raise AssertionError("top_k=0 must be rejected.")


def test_top_k_above_maximum_is_rejected():
    try:
        QueryRequest(question="What is RAG?", top_k=21)
    except ValidationError:
        return

    raise AssertionError("top_k=21 must be rejected.")
