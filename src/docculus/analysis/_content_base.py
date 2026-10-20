r"""Provide the state and logic shared by the content statistics
accumulators."""

from __future__ import annotations

__all__ = ["ContentStatsBase", "content_hash", "nearest_rank_percentile"]

import hashlib
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from docculus.document import get_length

if TYPE_CHECKING:
    from langchain_core.documents import Document


def content_hash(content: str) -> bytes:
    r"""Compute a 16-byte BLAKE2b digest of ``content``.

    Lone surrogates are preserved (``surrogatepass``), so distinct
    strings never share an encoding. 128 bits is ample to make
    accidental collisions negligible while halving the memory used to
    track seen contents.

    Args:
        content: The text to hash.

    Returns:
        The 16-byte digest.
    """
    return hashlib.blake2b(content.encode("utf-8", errors="surrogatepass"), digest_size=16).digest()


def nearest_rank_percentile(sorted_values: list[int], p: float) -> float | None:
    r"""Compute a percentile from a pre-sorted list.

    Uses the nearest-rank method: the index into ``sorted_values`` is
    ``p / 100 * (n - 1)`` rounded half up (not Python's banker's
    rounding, so the result does not depend on the parity of the
    index). This returns an element of the data and differs from the
    linear interpolation used by ``numpy.percentile``.

    Args:
        sorted_values: Values sorted in ascending order.
        p: Percentile to compute, in the range ``[0, 100]``.

    Returns:
        The value at the requested percentile, or ``None`` if
        ``sorted_values`` is empty.
    """
    if not sorted_values:
        return None
    return sorted_values[math.floor(p / 100 * (len(sorted_values) - 1) + 0.5)]


@dataclass(slots=True)
class ContentStatsBase:
    """Hold the counters and length extremes shared by
    ``ExactContentStats`` and ``ApproxContentStats``.

    See the subclasses for the description of each attribute.
    """

    count: int = 0
    total_chars: int = 0
    min_chars: int | None = None
    max_chars: int | None = None
    min_doc_id: Any | None = None
    max_doc_id: Any | None = None

    empty_count: int = 0
    whitespace_only_count: int = 0
    none_or_non_str_content_count: int = 0
    none_id_count: int = 0
    missing_metadata_count: int = 0

    def _update_base(self, doc: Document) -> tuple[str, int]:
        """Fold the exact counters and extremes of ``doc`` into the
        state.

        Args:
            doc: The document to process.

        Returns:
            A ``(content, length)`` tuple, where ``content`` is the
            document's ``page_content`` (``""`` if it is not a string)
            and ``length`` is its length in characters.
        """
        doc_id = doc.id
        if doc_id is None:
            self.none_id_count += 1

        content = doc.page_content
        if not isinstance(content, str):
            self.none_or_non_str_content_count += 1
            content = ""

        if content == "":
            self.empty_count += 1
        elif content.strip() == "":
            self.whitespace_only_count += 1

        if not doc.metadata:
            self.missing_metadata_count += 1

        length = get_length(doc)
        self.count += 1
        self.total_chars += length

        if self.min_chars is None or length < self.min_chars:
            self.min_chars, self.min_doc_id = length, doc_id
        if self.max_chars is None or length > self.max_chars:
            self.max_chars, self.max_doc_id = length, doc_id
        return content, length
