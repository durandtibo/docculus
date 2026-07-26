r"""Contain document utilities."""

from __future__ import annotations

__all__ = [
    "get_id_lengths",
    "get_length",
    "get_lengths",
    "get_longest_document",
    "get_shortest_document",
    "is_empty",
    "is_whitespace_only",
]

from docculus.document.empty import is_empty, is_whitespace_only
from docculus.document.length import (
    get_id_lengths,
    get_length,
    get_lengths,
    get_longest_document,
    get_shortest_document,
)
