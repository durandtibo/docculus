from __future__ import annotations

import pytest
from langchain_core.documents import Document

from docculus.document import generate_deterministic_id, generate_id, generate_random_id

#####################################
#     Tests for generate_id         #
#####################################


def test_generate_id_default_mode_is_deterministic() -> None:
    doc = Document(page_content="Hello", metadata={"source": "cats.txt"})
    assert generate_id(doc) == generate_deterministic_id(doc)


def test_generate_id_deterministic_mode() -> None:
    doc = Document(page_content="Hello", metadata={"source": "cats.txt"})
    assert generate_id(doc, mode="deterministic") == generate_deterministic_id(doc)


def test_generate_id_random_mode() -> None:
    doc = Document(page_content="Hello")
    assert isinstance(generate_id(doc, mode="random"), str)


def test_generate_id_random_mode_different_calls_differ() -> None:
    doc = Document(page_content="Hello")
    assert generate_id(doc, mode="random") != generate_id(doc, mode="random")


def test_generate_id_invalid_mode_raises() -> None:
    doc = Document(page_content="Hello")
    with pytest.raises(ValueError, match="Invalid mode"):
        generate_id(doc, mode="unknown")


def test_generate_id_returns_str() -> None:
    doc = Document(page_content="Hello")
    assert isinstance(generate_id(doc), str)


#################################################
#     Tests for generate_deterministic_id       #
#################################################


def test_generate_deterministic_id_returns_str() -> None:
    doc = Document(page_content="Hello")
    assert isinstance(generate_deterministic_id(doc), str)


def test_generate_deterministic_id_same_content_same_id() -> None:
    doc1 = Document(page_content="Hello", metadata={"source": "cats.txt"})
    doc2 = Document(page_content="Hello", metadata={"source": "cats.txt"})
    assert generate_deterministic_id(doc1) == generate_deterministic_id(doc2)


def test_generate_deterministic_id_different_content_different_id() -> None:
    doc1 = Document(page_content="Hello")
    doc2 = Document(page_content="World")
    assert generate_deterministic_id(doc1) != generate_deterministic_id(doc2)


def test_generate_deterministic_id_different_metadata_different_id() -> None:
    doc1 = Document(page_content="Hello", metadata={"source": "cats.txt"})
    doc2 = Document(page_content="Hello", metadata={"source": "dogs.txt"})
    assert generate_deterministic_id(doc1) != generate_deterministic_id(doc2)


def test_generate_deterministic_id_stable_across_calls() -> None:
    doc = Document(page_content="Hello", metadata={"source": "cats.txt"})
    first = generate_deterministic_id(doc)
    second = generate_deterministic_id(doc)
    assert first == second


def test_generate_deterministic_id_ignores_original_id() -> None:
    doc1 = Document(page_content="Hello", id="id-1")
    doc2 = Document(page_content="Hello", id="id-2")
    assert generate_deterministic_id(doc1) == generate_deterministic_id(doc2)


#############################################
#     Tests for generate_random_id          #
#############################################


def test_generate_random_id_returns_str() -> None:
    assert isinstance(generate_random_id(), str)


def test_generate_random_id_returns_uuid_length() -> None:
    assert len(generate_random_id()) == 36


def test_generate_random_id_different_each_call() -> None:
    assert generate_random_id() != generate_random_id()
