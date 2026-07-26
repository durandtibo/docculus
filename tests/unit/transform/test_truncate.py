r"""Contain unit tests for ``docculus.transform.truncate``."""

from __future__ import annotations

from langchain_core.documents import Document

from docculus.transform.truncate import truncate_documents


def test_truncate_documents_shorter_than_max_length_is_unchanged() -> None:
    docs = [Document(page_content="hello")]
    result = truncate_documents(docs, max_length=10)
    assert [doc.page_content for doc in result] == ["hello"]


def test_truncate_documents_longer_than_max_length_is_truncated() -> None:
    docs = [Document(page_content="hello world")]
    result = truncate_documents(docs, max_length=5)
    assert [doc.page_content for doc in result] == ["hello"]


def test_truncate_documents_with_suffix_stays_within_max_length() -> None:
    docs = [Document(page_content="hello world")]
    result = truncate_documents(docs, max_length=8, suffix="...")
    assert [doc.page_content for doc in result] == ["hello..."]


def test_truncate_documents_with_suffix_not_applied_when_not_truncated() -> None:
    docs = [Document(page_content="hi")]
    result = truncate_documents(docs, max_length=10, suffix="...")
    assert [doc.page_content for doc in result] == ["hi"]


def test_truncate_documents_preserves_id_and_metadata() -> None:
    docs = [Document(id="a", page_content="hello world", metadata={"source": "x"})]
    result = truncate_documents(docs, max_length=5)
    assert result[0].id == "a"
    assert result[0].metadata == {"source": "x"}


def test_truncate_documents_non_string_page_content_treated_as_empty() -> None:
    doc = Document(page_content="placeholder")
    doc.page_content = None
    result = truncate_documents([doc], max_length=5)
    assert result[0].page_content == ""


def test_truncate_documents_empty_list() -> None:
    assert truncate_documents([], max_length=5) == []


def test_truncate_documents_does_not_modify_original_documents() -> None:
    docs = [Document(page_content="hello world")]
    truncate_documents(docs, max_length=5)
    assert docs[0].page_content == "hello world"
