r"""Contain utilities to transform documents."""

from __future__ import annotations

__all__ = [
    "assign_ids",
    "copy_ids_to_metadata",
    "deduplicate_documents",
    "filter_by_metadata",
    "filter_by_metadata_range",
    "filter_by_metadata_values",
    "sort_by_metadata",
]

from docculus.transform.dedup import deduplicate_documents
from docculus.transform.filter import (
    filter_by_metadata,
    filter_by_metadata_range,
    filter_by_metadata_values,
)
from docculus.transform.id import assign_ids, copy_ids_to_metadata
from docculus.transform.sort import sort_by_metadata
