r"""Contain hashing utilities."""

from __future__ import annotations

__all__ = ["hash_document", "hash_document_uuid", "hash_documents"]

from docculus.hashing.hashing import hash_document, hash_documents
from docculus.hashing.uuid import hash_document_uuid
