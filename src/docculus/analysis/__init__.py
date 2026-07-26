r"""Contain utilities to compute document statistics."""

from __future__ import annotations

__all__ = [
    "ApproxContentStats",
    "ExactContentStats",
    "MetadataStats",
    "compute_content_stats_approx",
    "compute_content_stats_exact",
    "compute_metadata_stats",
    "find_duplicate_content_document_ids",
    "find_empty_document_ids",
    "find_empty_documents",
    "print_content_stats_report",
    "print_metadata_stats_report",
]

from docculus.analysis.content_approx import (
    ApproxContentStats,
    compute_content_stats_approx,
)
from docculus.analysis.content_exact import (
    ExactContentStats,
    compute_content_stats_exact,
)
from docculus.analysis.content_print import print_content_stats_report
from docculus.analysis.duplicate import find_duplicate_content_document_ids
from docculus.analysis.empty import (
    find_empty_document_ids,
    find_empty_documents,
)
from docculus.analysis.metadata_print import print_metadata_stats_report
from docculus.analysis.metadata_stats import (
    MetadataStats,
    compute_metadata_stats,
)
