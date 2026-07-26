# Corpus Analysis

:book: This page describes the `docculus.analysis` package, which provides read-only,
corpus-wide inspection utilities: statistics, duplicate/empty detection, and report printing.

**Prerequisites:** You'll need to know a bit of Python and be familiar with
[LangChain](https://python.langchain.com/) `Document` objects.

## Overview

Functions in `docculus.analysis` consume an iterable of documents and never mutate the input or
return a new document list -- they answer questions about a corpus. For per-document predicates,
see [`docculus.document`](hashing.md); for functions that produce a new document list (dedup,
filter, sort, format), see the [transform user guide](transform.md).

Every function here is streaming: documents are consumed one at a time, so they work with
generators or other iterables whose full contents cannot fit in memory. Consuming a generator or
iterator exhausts it -- pass a fresh iterable (or a `list`) if you need to run more than one
analysis over the same documents.

## Duplicate and Empty Documents

`find_duplicate_document_ids` groups the `id`s of documents that share exactly the same
`page_content`:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.analysis import find_duplicate_document_ids
>>> docs = [
...     Document(id="a", page_content="hello"),
...     Document(id="b", page_content="hello"),
...     Document(id="c", page_content="world"),
... ]
>>> find_duplicate_document_ids(docs)
[['a', 'b']]

```

`find_empty_documents`/`find_empty_document_ids` return the documents (or just their `id`s) whose
`page_content` is empty, optionally treating whitespace-only content as empty too:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.analysis import find_empty_document_ids
>>> docs = [Document(id="a", page_content="hello"), Document(id="b", page_content="")]
>>> find_empty_document_ids(docs)
['b']

```

## Content Statistics

`compute_content_stats_exact` computes length, duplicate, and data-quality statistics over a
corpus, with exact duplicate detection and exact percentiles:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.analysis import compute_content_stats_exact
>>> docs = [
...     Document(id="a", page_content="hello"),
...     Document(id="b", page_content="hello world"),
... ]
>>> stats = compute_content_stats_exact(docs)
>>> stats["count"]
2

```

`compute_content_stats_approx` is an approximate variant with fixed (`O(1)`) memory usage,
suitable for corpora too large for the exact hash set and length list to fit in memory. It uses a
Bloom filter for duplicate detection (never under-counts, but may over-count near the configured
`fp_rate`) and reservoir sampling for percentiles:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.analysis import compute_content_stats_approx
>>> docs = [
...     Document(id="a", page_content="hello"),
...     Document(id="b", page_content="hello world"),
... ]
>>> stats = compute_content_stats_approx(docs, expected_doc_count=1000, fp_rate=0.01)
>>> stats["count"]
2

```

## Metadata Statistics

`compute_metadata_stats` computes per-key metadata coverage and sample values across a corpus:

```pycon
>>> from langchain_core.documents import Document
>>> from docculus.analysis import compute_metadata_stats
>>> docs = [
...     Document(page_content="a", metadata={"source": "a.pdf"}),
...     Document(page_content="b", metadata={"source": "b.pdf", "page": 1}),
... ]
>>> stats = compute_metadata_stats(docs)
>>> stats["count"]
2

```

`n_sample_values` (default `3`) caps how many unique sample values are retained per metadata key;
pass `None` to track every unique value instead, at the cost of unbounded memory per key.

## Printing Reports to the Terminal

`print_content_stats_report` and `print_metadata_stats_report` render the dicts returned by the
functions above as a `rich` panel in the terminal (requires the `rich` extra,
`docculus[rich]`):

```python
from docculus.analysis import compute_content_stats_exact, print_content_stats_report

stats = compute_content_stats_exact(docs)
print_content_stats_report(stats, title="Corpus Content Report")
```

```python
from docculus.analysis import compute_metadata_stats, print_metadata_stats_report

stats = compute_metadata_stats(docs)
print_metadata_stats_report(stats)
```

`print_content_stats_report` automatically detects whether the report is exact or approximate
(from the `duplicate_count_exact`/`percentiles_exact` keys in `stats`) and labels the panel
accordingly, including a footnote about the Bloom-filter false-positive rate for approximate
reports.

## API Reference

See the [reference documentation](../refs/analysis.md) for the full API.
