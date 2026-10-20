r"""Contain utilities to transform documents.

Mutation semantics:

- ``assign_ids`` and ``copy_ids_to_metadata`` modify the given
  documents in place and return the same list.
- ``truncate_documents`` returns new ``Document`` objects (with copied
  metadata).
- All other functions return a new list (or string) and never modify
  their input, but the returned list may contain the same ``Document``
  objects as the input.
"""

from __future__ import annotations

__all__ = [
    "assign_ids",
    "copy_ids_to_metadata",
    "deduplicate_documents",
    "filter_by_metadata",
    "filter_by_metadata_range",
    "filter_by_metadata_values",
    "format_documents",
    "format_documents_as_json",
    "format_documents_as_markdown",
    "format_documents_as_xml",
    "sort_by_metadata",
    "truncate_documents",
]

from docculus.transform.dedup import deduplicate_documents
from docculus.transform.filter import (
    filter_by_metadata,
    filter_by_metadata_range,
    filter_by_metadata_values,
)
from docculus.transform.format import (
    format_documents,
    format_documents_as_json,
    format_documents_as_markdown,
    format_documents_as_xml,
)
from docculus.transform.id import assign_ids, copy_ids_to_metadata
from docculus.transform.sort import sort_by_metadata
from docculus.transform.truncate import truncate_documents
