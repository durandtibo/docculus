r"""Provide the canonical string used to hash a document."""

from __future__ import annotations

__all__ = ["canonical_document_string"]

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.documents import Document


def canonical_document_string(doc: Document) -> str:
    r"""Serialize a document's content and metadata unambiguously.

    Content and metadata are encoded together as one JSON object with
    sorted keys, so no ``(page_content, metadata)`` pair can produce the
    same string as a different pair, and metadata insertion order does
    not matter. Metadata values that are not JSON-serializable are
    converted with :func:`str`.

    Args:
        doc: The document to serialize.

    Returns:
        The canonical JSON string.
    """
    return json.dumps(
        {"page_content": doc.page_content, "metadata": doc.metadata},
        sort_keys=True,
        default=str,
    )
