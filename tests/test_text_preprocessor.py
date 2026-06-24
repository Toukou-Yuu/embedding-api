from __future__ import annotations

from app.schemas import InputType
from app.services.text_preprocessor import preprocess_texts


def test_intfloat_prefixes_are_applied_by_embedding_api() -> None:
    assert preprocess_texts("intfloat/e5-base", ["question"], InputType.QUERY) == [
        "query: question"
    ]
    assert preprocess_texts("intfloat/e5-base", ["document"], InputType.DOCUMENT) == [
        "passage: document"
    ]


def test_bge_m3_does_not_receive_an_uncertain_prefix() -> None:
    assert preprocess_texts("BAAI/bge-m3", ["text"], InputType.QUERY) == ["text"]
