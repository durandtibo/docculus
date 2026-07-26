from __future__ import annotations

import pytest
from coola.hashing import HasherRegistry
from langchain_core.documents import Document

from docculus.hashing import DocumentHasher, hash_document


@pytest.fixture
def registry() -> HasherRegistry:
    return HasherRegistry()


####################################
#     Tests for DocumentHasher     #
####################################


def test_document_hasher_repr() -> None:
    assert repr(DocumentHasher()) == "DocumentHasher()"


def test_document_hasher_str() -> None:
    assert str(DocumentHasher()) == "DocumentHasher()"


def test_document_hasher_hash_returns_str(registry: HasherRegistry) -> None:
    hasher = DocumentHasher()
    assert isinstance(hasher.hash(Document(page_content="Hello"), registry=registry), str)


def test_document_hasher_hash_default_length(registry: HasherRegistry) -> None:
    hasher = DocumentHasher()
    assert len(hasher.hash(Document(page_content="Hello"), registry=registry)) == 64


@pytest.mark.parametrize(
    "length",
    [
        pytest.param(2, id="min-valid"),
        pytest.param(32, id="middle"),
        pytest.param(64, id="default"),
        pytest.param(128, id="max-valid"),
    ],
)
def test_document_hasher_hash_length(registry: HasherRegistry, length: int) -> None:
    hasher = DocumentHasher()
    assert (
        len(hasher.hash(Document(page_content="Hello"), registry=registry, length=length)) == length
    )


def test_document_hasher_hash_same_document_same_hash(registry: HasherRegistry) -> None:
    hasher = DocumentHasher()
    doc = Document(page_content="Hello", metadata={"source": "cats.txt"})
    assert hasher.hash(doc, registry=registry) == hasher.hash(doc, registry=registry)


def test_document_hasher_hash_equal_documents_same_hash(registry: HasherRegistry) -> None:
    hasher = DocumentHasher()
    doc_a = Document(page_content="Hello", metadata={"source": "cats.txt"})
    doc_b = Document(page_content="Hello", metadata={"source": "cats.txt"})
    assert hasher.hash(doc_a, registry=registry) == hasher.hash(doc_b, registry=registry)


def test_document_hasher_hash_different_content_different_hash(registry: HasherRegistry) -> None:
    hasher = DocumentHasher()
    doc_a = Document(page_content="Hello", metadata={"source": "cats.txt"})
    doc_b = Document(page_content="World", metadata={"source": "cats.txt"})
    assert hasher.hash(doc_a, registry=registry) != hasher.hash(doc_b, registry=registry)


def test_document_hasher_hash_different_metadata_different_hash(registry: HasherRegistry) -> None:
    hasher = DocumentHasher()
    doc_a = Document(page_content="Hello", metadata={"source": "cats.txt"})
    doc_b = Document(page_content="Hello", metadata={"source": "dogs.txt"})
    assert hasher.hash(doc_a, registry=registry) != hasher.hash(doc_b, registry=registry)


def test_document_hasher_hash_metadata_order_independent(registry: HasherRegistry) -> None:
    hasher = DocumentHasher()
    doc_a = Document(page_content="Hello", metadata={"source": "cats.txt", "category": "Science"})
    doc_b = Document(page_content="Hello", metadata={"category": "Science", "source": "cats.txt"})
    assert hasher.hash(doc_a, registry=registry) == hasher.hash(doc_b, registry=registry)


def test_document_hasher_hash_matches_hash_document(registry: HasherRegistry) -> None:
    hasher = DocumentHasher()
    doc = Document(page_content="Hello", metadata={"source": "cats.txt"})
    assert hasher.hash(doc, registry=registry) == hash_document(doc)


def test_document_hasher_hash_matches_hash_document_with_length(registry: HasherRegistry) -> None:
    hasher = DocumentHasher()
    doc = Document(page_content="Hello", metadata={"source": "cats.txt"})
    assert hasher.hash(doc, registry=registry, length=32) == hash_document(doc, length=32)


def test_document_hasher_hash_ignores_registry(registry: HasherRegistry) -> None:
    """The registry is accepted for interface compatibility but should
    not affect the resulting hash, since DocumentHasher delegates
    entirely to hash_document."""
    hasher = DocumentHasher()
    doc = Document(page_content="Hello", metadata={"source": "cats.txt"})
    assert hasher.hash(doc, registry=HasherRegistry()) == hasher.hash(doc, registry=registry)
