r"""Content approximate document statistics."""

from __future__ import annotations

__all__ = ["ApproxContentStats", "compute_content_stats_approx"]

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from coola.utils.bloom_filter import BloomFilter

from docculus.analysis._content_base import (
    ContentStatsBase,
    content_hash,
    nearest_rank_percentile,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from langchain_core.documents import Document


@dataclass(slots=True)
class ApproxContentStats(ContentStatsBase):
    """Streaming document health/analysis with APPROXIMATE duplicate
    detection and APPROXIMATE percentiles.

    Accumulates statistics one document at a time via ``update``, so it
    can be fed from a list, a generator, or any other iterable without
    requiring the full corpus to be held in memory at once. Call
    ``to_dict`` at the end to compute the final report.

    Unlike ``ExactContentStats``, memory usage here is fixed (O(1)
    per document, i.e. does not grow with the number of documents
    processed): duplicate detection uses a ``BloomFilter`` sized up
    front from an expected document count, and percentiles are
    estimated from a fixed-size reservoir sample of lengths rather than
    the full list. This trades a small, bounded amount of accuracy for
    a memory profile suitable for corpora too large to fit exact
    per-document data (hashes, lengths) in memory.

    Attributes:
        count: Total number of documents processed.
        total_chars: Sum of ``page_content`` lengths across all
            documents processed.
        min_chars: Length, in characters, of the shortest
            ``page_content`` seen so far, or ``None`` if no documents
            have been processed yet.
        max_chars: Length, in characters, of the longest
            ``page_content`` seen so far, or ``None`` if no documents
            have been processed yet.
        min_doc_id: ``id`` of the document with the shortest
            ``page_content`` seen so far (first one seen, in case of a
            tie), or ``None`` if no documents have been processed yet.
        max_doc_id: ``id`` of the document with the longest
            ``page_content`` seen so far (first one seen, in case of a
            tie), or ``None`` if no documents have been processed yet.
        empty_count: Number of documents whose ``page_content`` is the
            empty string (or was coerced to it, e.g. ``None`` content).
        whitespace_only_count: Number of documents whose
            ``page_content`` is non-empty but contains only whitespace.
        none_or_non_str_content_count: Number of documents whose
            ``page_content`` was not a string (e.g. ``None`` or another
            type). Such content is treated as an empty string for all
            other statistics.
        none_id_count: Number of documents whose ``id`` is ``None``.
        missing_metadata_count: Number of documents whose ``metadata``
            is empty or falsy.
        seed: Optional seed for the private random generator used by
            the reservoir sampling.
        bloom: An optional pre-built ``BloomFilter``. If ``None``, one
            is created from ``expected_doc_count`` and ``fp_rate``.
        approx_duplicate_count: Approximate number of documents whose
            exact ``page_content`` has already been seen earlier in the
            stream, as reported by the Bloom filter. Never
            undercounts by much; may slightly overcount due to the
            filter's false-positive rate.
    """

    approx_duplicate_count: int = 0

    expected_doc_count: int = 1_000_000
    fp_rate: float = 0.01
    reservoir_size: int = 10_000
    seed: int | None = None
    bloom: BloomFilter | None = None

    _reservoir: list[int] = field(default_factory=list, init=False, repr=False)
    _seen_for_reservoir: int = field(default=0, init=False, repr=False)
    _mean: float = field(default=0.0, init=False, repr=False)
    _m2: float = field(default=0.0, init=False, repr=False)
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Construct the Bloom filter (if one wasn't supplied) from the
        configured ``expected_doc_count`` and ``fp_rate``, and the
        private random generator from ``seed``."""
        if self.bloom is None:
            self.bloom = BloomFilter(expected_items=self.expected_doc_count, fp_rate=self.fp_rate)
        self._rng = random.Random(self.seed)  # noqa: S311

    def update(self, doc: Document) -> None:
        """Fold a single document into the running statistics.

        Updates all counters, the min/max character length (with the
        associated document id), the Bloom filter used for approximate
        duplicate detection, and the reservoir sample of lengths used
        later for approximate percentile
        calculations.

        Args:
            doc: The document to process. Its ``id`` is assumed to
                always be present as an attribute (though its value may
                be ``None``). Its ``page_content`` is expected to be a
                string; non-string content (including ``None``) is
                counted via ``none_or_non_str_content_count`` and
                treated as an empty string for length, emptiness, and
                duplicate calculations. Its ``metadata`` is expected to
                be a mapping; a falsy/empty mapping is counted via
                ``missing_metadata_count``.
        """
        content, length = self._update_base(doc)

        assert self.bloom is not None  # noqa: S101 (set in __post_init__)
        if self.bloom.add_and_check(content_hash(content)):
            self.approx_duplicate_count += 1

        # Welford's online algorithm: exact mean and variance in O(1) memory.
        delta = length - self._mean
        self._mean += delta / self.count
        self._m2 += delta * (length - self._mean)

        self._update_reservoir(length)

    def _update_reservoir(self, length: int) -> None:
        """Add a length to the reservoir sample."""
        # Reservoir sampling (Algorithm R): keeps a uniform random sample
        # of up to `reservoir_size` lengths seen so far, in O(1) memory
        # relative to the total number of documents processed.
        self._seen_for_reservoir += 1
        if len(self._reservoir) < self.reservoir_size:
            self._reservoir.append(length)
        else:
            j = self._rng.randint(0, self._seen_for_reservoir - 1)
            if j < self.reservoir_size:
                self._reservoir[j] = length

    def to_dict(self) -> dict[str, Any]:
        """Compute the final statistics report from the accumulated
        state.

        Derives the average from the exact running total, and the
        exact (population) standard deviation, and the 50th/90th/99th
        percentiles of content length from the reservoir sample. Safe to
        call multiple times and at any point during accumulation; it
        does not mutate any state and always reflects everything
        processed via ``update`` so far.

        Returns:
            A dict with the following keys:

            - ``count``: Total number of documents processed (exact).
            - ``total_chars``: Sum of all ``page_content`` lengths
              (exact).
            - ``avg_chars``: Mean ``page_content`` length (exact), or
              ``0`` if no documents were processed.
            - ``std_dev_chars``: Population standard deviation of
              ``page_content`` length (exact, computed online with
              Welford's algorithm); ``0`` if
              fewer than two documents were processed.
            - ``min_chars`` / ``max_chars``: Shortest/longest
              ``page_content`` length seen (exact), or ``None`` if
              empty.
            - ``min_doc_id`` / ``max_doc_id``: ``id`` of the
              shortest/longest document seen (exact), or ``None`` if
              empty.
            - ``p50_chars_approx`` / ``p90_chars_approx`` /
              ``p99_chars_approx``: Estimated 50th/90th/99th percentile
              of ``page_content`` length, or ``None`` if empty.
            - ``empty_count``: Number of documents with empty content
              (exact).
            - ``whitespace_only_count``: Number of documents with
              whitespace-only content (exact).
            - ``none_or_non_str_content_count``: Number of documents
              whose content was not a string (exact).
            - ``none_id_count``: Number of documents with a ``None``
              id (exact).
            - ``missing_metadata_count``: Number of documents with
              empty/missing metadata (exact).
            - ``approx_duplicate_count``: Approximate number of
              documents that duplicate the content of an earlier
              document, as reported by the Bloom filter.
            - ``duplicate_count_exact``: Always ``False``; marks this
              report as using approximate (not exact) deduplication.
            - ``percentiles_exact``: Always ``False``; marks the
              percentiles above as estimated (not exact) values.
            - ``bloom_filter_fp_rate``: The configured target
              false-positive rate of the Bloom filter used for
              duplicate detection, for reference when interpreting
              ``approx_duplicate_count``.
            - ``reservoir_sample_size``: The number of lengths actually
              held in the reservoir sample used for the percentile
              estimates (``min(count,
              reservoir_size)``).
        """
        n = self.count
        avg = self.total_chars / n if n else 0

        sample = self._reservoir
        std_dev = (self._m2 / n) ** 0.5 if n > 1 else 0.0

        sorted_sample = sorted(sample)

        return {
            "count": n,
            "total_chars": self.total_chars,
            "avg_chars": avg,
            "std_dev_chars": std_dev,
            "min_chars": self.min_chars,
            "max_chars": self.max_chars,
            "min_doc_id": self.min_doc_id,
            "max_doc_id": self.max_doc_id,
            "p50_chars_approx": nearest_rank_percentile(sorted_sample, 50),
            "p90_chars_approx": nearest_rank_percentile(sorted_sample, 90),
            "p99_chars_approx": nearest_rank_percentile(sorted_sample, 99),
            "empty_count": self.empty_count,
            "whitespace_only_count": self.whitespace_only_count,
            "none_or_non_str_content_count": self.none_or_non_str_content_count,
            "none_id_count": self.none_id_count,
            "missing_metadata_count": self.missing_metadata_count,
            "approx_duplicate_count": self.approx_duplicate_count,
            "duplicate_count_exact": False,
            "percentiles_exact": False,
            "bloom_filter_fp_rate": self.fp_rate,
            "reservoir_sample_size": len(sample),
        }


def compute_content_stats_approx(
    documents: Iterable[Document],
    *,
    expected_doc_count: int = 1_000_000,
    fp_rate: float = 0.01,
    reservoir_size: int = 10_000,
    seed: int | None = None,
) -> dict[str, Any]:
    """Compute approximate content health/statistics over a stream of
    documents, using fixed (O(1)) memory regardless of corpus size.

    Streaming health/stat check over a list, generator, or any iterable
    of Documents, with APPROXIMATE duplicate detection (via a Bloom
    filter) and APPROXIMATE percentiles (via reservoir sampling).
    Documents are consumed one at a time, so this works with iterators
    or generators whose full contents cannot fit in memory. Unlike
    ``compute_content_stats_exact``, memory usage here does not
    grow with the number of documents processed, only with the
    configured ``expected_doc_count``, ``fp_rate``, and
    ``reservoir_size`` — making this the appropriate choice for corpora
    too large for exact per-document hashes/lengths to fit in memory.

    Args:
        documents: A list, generator, or other iterable of
            ``langchain_core.documents.Document`` objects. Consumed
            exactly once; if a generator/iterator is passed in, it will
            be exhausted by this call.
        expected_doc_count: Rough estimate of the total number of
            documents (or, more precisely, unique documents) that will
            be processed. Used to size the Bloom filter for the
            requested ``fp_rate``. Safe to overestimate; underestimating
            causes the effective false-positive rate to rise above
            ``fp_rate`` as more documents are processed than planned
            for.
        fp_rate: Target false-positive probability for duplicate
            detection, once approximately ``expected_doc_count``
            unique documents have been added. The Bloom filter never
            produces false negatives, so ``approx_duplicate_count``
            never undercounts true duplicates by more than this rate
            would suggest, though it may overcount slightly.
        reservoir_size: Number of lengths to retain in the reservoir
            sample used to estimate the percentiles. Larger values
            improve estimate accuracy at the cost of more memory; the
            memory cost is still fixed (independent of the number of
            documents processed).
        seed: Optional seed for the reservoir sampling, for
            reproducible percentile estimates. If ``None``, sampling
            is not reproducible. Uses a private random generator, so
            the global :mod:`random` state is neither read nor
            modified.

    Returns:
        A dict of statistics as described in
        ``ApproxContentStats.to_dict``. For an empty input, returns
        a report with ``count`` of ``0`` and ``None``/``0`` values for
        the length-based fields.

    Example:
        ```pycon
        >>> from langchain_core.documents import Document
        >>> from docculus.analysis import compute_content_stats_approx
        >>> docs = [
        ...     Document(id="a", page_content="hello"),
        ...     Document(id="b", page_content="hello world"),
        ... ]
        >>> analysis = compute_content_stats_approx(docs, expected_doc_count=1000)
        >>> analysis["count"]
        2

        ```

    See Also:
        ``compute_content_stats_exact``: an exact variant using a
        hash set for duplicate detection and a full sorted list of
        lengths for percentiles, with memory usage that grows with
        corpus size but produces exact (non-approximate) results.
    """
    stats = ApproxContentStats(
        expected_doc_count=expected_doc_count,
        fp_rate=fp_rate,
        reservoir_size=reservoir_size,
        seed=seed,
    )
    for doc in documents:
        stats.update(doc)
    return stats.to_dict()
