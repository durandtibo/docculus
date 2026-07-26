r"""Contain store utilities for docculus."""

from __future__ import annotations

__all__ = ["BaseDocumentStore", "DocumentStore", "SQLiteDocumentStore", "TypedSQLiteDocumentStore"]

from docculus.store.base import BaseDocumentStore
from docculus.store.custom import SQLiteDocumentStore, TypedSQLiteDocumentStore
from docculus.store.document import DocumentStore
