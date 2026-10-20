# Codebase review: suggestions

Scope: every module under `src/docculus/`, plus `examples/`, `pyproject.toml`, the docs layout, the tests layout and the CI/tooling layout. I read the source in full. The items were found by reading the code, not by running the test suite or the linters. Items are grouped by priority.

**Progress:** sections 1 (likely bugs), 2 (design and API consistency) and 3 (performance and memory) have been worked on; each item carries a status line. Sections 4 to 7 have not been started. Items marked "fixed" are covered by tests and the suite stays at 100% coverage. Line references below refer to the code as it was when reviewed, before these fixes.

## 1. Likely bugs (fix first)

### 1.1 Rich markup injection in the display helpers

**Status: fixed.** All interpolated ids, keys and values are escaped with `rich.markup.escape` in the four display/report modules; regression test added.

`display/document.py:125-129`, `display/metadata.py:262`, `display/document.py:140`

Metadata keys, metadata values and `doc.id` are interpolated into strings that are then parsed as Rich markup (`Text.from_markup(f"[bold]{key}[/bold]: {value}")`, `f"[cyan]{doc.id}[/cyan]"`).

- A value such as `"[/foo]"` or `"[link=x]"` raises `rich.errors.MarkupError` or renders wrongly.
- A value like `"array[0]"` is silently eaten.

Fix: wrap interpolated values in `rich.markup.escape(str(...))`, or build `Text` objects with `.append(key, style="bold")` instead of parsing markup. The same applies to `analysis/content_print.py` (doc ids in `_build_doc_ids_grid` go into a `Table` cell, which is parsed as markup) and to `analysis/metadata_print.py` (keys and sample values in the per-key table).

### 1.2 Hash and UUID collisions from ambiguous concatenation

**Status: fixed, with one follow-up left.** Content and metadata are now hashed as one JSON object (shared helper `hashing/_canonical.py`, `default=str` for non-JSON metadata), so the two hashing functions can no longer drift. Not done: a library-wide policy for non-string `page_content` in the hashing functions. Existing ids and hashes change.

`hashing/functions.py:795`, `hashing/uuid.py:948`

`doc.page_content + json.dumps(doc.metadata, sort_keys=True)` has no separator or length prefix, so the boundary between content and metadata is not encoded in the hashed string. I could not construct a concrete collision (the metadata JSON always starts with `{` and ends with `}`, which makes real collisions contrived), so this is a robustness issue more than a demonstrated bug: any scheme that relies on that implicit boundary is hard to reason about. Deterministic ids are meant to be an idempotent-upsert key, so a collision means silent data loss in the store.

Fix: hash a structured encoding, e.g. `json.dumps({"c": content, "m": metadata}, sort_keys=True)`, or prefix the content length. This changes every existing id, so do it before 1.0 and note it in the changelog.

Related:

- `hash_document` and `hash_document_to_uuid` duplicate the same canonicalization. Extract one `_canonical_string(doc)` helper so the two cannot drift.
- `json.dumps` raises `TypeError` on non-JSON-serializable metadata (datetimes, `Path`, numpy scalars). Either pass `default=str` (documented) or document and test the exception. The same applies to `deduplicate_documents` and `validate_document_consistency`.
- `page_content` is assumed to be `str` here, although `is_empty`, `get_length`, `truncate_documents` and the stats classes all defend against `None`. Pick one policy for the whole library.

### 1.3 `sort_by_metadata` reuses the name `missing` for two things

**Status: fixed.** The name clash and the dead sentinel are gone. Not done: treating an explicit `None` value as missing.

`transform/sort.py:2595-2606`

`missing = object()` is the sentinel captured by the `sort_key` closure, and a few lines later `missing = [doc for ...]` rebinds the name to a list. The closure now compares against that list. It works today only because every document passed to `sorted` has the key, so the sentinel branch is never hit. Any refactor that changes this breaks silently.

- Rename the list to `missing_docs`.
- Simplify: since missing-key documents are always partitioned out, the sentinel and the tuple key are dead code. `key=lambda d: d.metadata[metadata_key]` is enough.

Also: a document with an explicit `None` value for the key makes `sorted` raise `TypeError` when mixed with other values. Decide whether `None` should be treated as missing (probably yes) and document it.

### 1.4 `copy_ids_to_metadata` doctest is wrong

**Status: fixed.** The example now assigns the returned list.

`transform/id.py:2514-2518`

`>>> copy_ids_to_metadata(docs)` returns the list, so the doctest prints a `[Document(...)]` repr that the expected output (nothing) does not match. Either assign the result or check why CI does not catch it (see 5.2).

### 1.5 `DocumentStore` flat mode has namespace and round-trip problems

**Status: partly fixed.** Done: reserved `page_content` key now raises in flat mode; typed stores reject metadata keys not in `metadata_schema`; JSON handling checked and left as is (consistent string round trip); empty `set_many` verified. Not done: documenting or changing the `None` round trip for typed stores, pushing `filter` down to SQL, and defining/testing behaviour for duplicate ids within one batch.

`store/document.py:1658-1674`

- In flat mode, `{_CONTENT_KEY: doc.page_content, **doc.metadata}` lets a metadata key named `page_content` silently overwrite the content. Raise `ValueError` on that key.
- In flat mode with typed SQL backends, every declared metadata column comes back on read, with `None` for absent fields. `get()` therefore returns `{"author": None}` where the document was written without `author`. Either drop `None` values on read (lossy for real nulls) or document the behaviour.
- In flat mode, metadata keys not declared in `metadata_schema` will fail inside the backend with a backend-specific error. Validate in `TypedSQLiteDocumentStore` and `TypedDuckDBDocumentStore` and raise a clear error.
- In single mode, `_to_value` does `json.dumps(doc.metadata)` and then stores the string in a column declared `JSON`. `_from_value` handles both `str` and already-decoded `dict`, which suggests the backend is inconsistent. Check how persista round-trips JSON columns and pick one representation, so the double encoding does not leak.
- `filter()` and `afilter()` load and decode the entire store in Python. That is fine for `InMemory`, but it defeats the point of the typed SQL stores, where flat mode could push `WHERE` clauses down. At minimum, document the full-scan cost. Better, add an optional `filter` hook to the persista `BaseStore` and use it when available.
- `set_many` with an empty list and with duplicate ids in one batch: confirm and test both behaviours. The dict comprehension silently keeps the last duplicate.

### 1.6 `find_duplicate_document_ids` treats non-string content as `""`

**Status: fixed.** Non-string content is skipped, `surrogatepass` is used everywhere, and the hash is shared in `analysis/_content_base.py`.

`analysis/dedup.py:1170`

A document with `page_content=None` is grouped with genuinely empty documents, and `errors="ignore"` on `encode` makes lone surrogates collapse to the same hash as the text without them. Skip non-string content (or report it separately), and use `errors="surrogatepass"` so distinct strings stay distinct. The same two lines are copied into `content_exact.py` and `content_approx.py`.

## 2. Design and API consistency

### 2.1 `list` versus `Iterable` parameter types

**Status: fixed.** `assign_ids` and `copy_ids_to_metadata` intentionally stay `list`, since they mutate in place and return the same list.

Analysis functions accept `Iterable[Document]` and say so. Most transform functions (`filter_*`, `sort_by_metadata`, `deduplicate_documents`, `assign_ids`, `format_documents*`, `validate_document_consistency`) take `list[Document]` although they only iterate once. Widen to `Iterable` (or `Sequence` where `len()` is needed) so generators from loaders work, and note which functions return a new list. `hash_documents` has to stay `list`/`Sequence` because order matters.

### 2.2 Mutating versus copying

**Status: mostly fixed.** `truncate_documents` copies metadata and the `transform` package docstring documents mutation semantics. Not done: an `inplace=False` option.

- `assign_ids` and `copy_ids_to_metadata` mutate in place and return the same list.
- `truncate_documents` returns new `Document` objects, but they share the original `metadata` dict (`metadata=doc.metadata`), so mutating a result mutates the input. Copy it with `dict(doc.metadata)`.
- Everything else returns new lists but the same `Document` objects.

Document this once in the `transform` package docstring. Consider offering a non-mutating `assign_ids(..., inplace=False)` or a `model_copy`-based variant. The in-place API forces callers who want purity to `deepcopy` first.

### 2.3 Boolean arguments should be keyword-only

**Status: fixed.** Breaking change for callers that passed these arguments positionally.

`deduplicate_documents(docs, log=False)`, `format_documents(documents, include_metadata=False, output_format="xml")`, `print_document(..., compact_metadata=False)` and `generate_fake_documents(n, seed, nb_sentences)` accept positional booleans or ints. Newer functions already use `*`. Make the rest consistent now, before the API is public.

### 2.4 String-typed modes should be `Literal`

**Status: fixed.** New `IdMode` and `OutputFormat` types.

`generate_id(doc, mode: str)`, `assign_ids(..., mode: str)`, `format_documents(output_format: str)`. Use `Literal["deterministic", "random"]` and `Literal["xml", "markdown", "json"]`, as `MetadataMode` already does. Type checkers then catch typos, and the error branches become the fallback for untyped callers only.

### 2.5 Format helpers (`transform/format.py`)

**Status: mostly fixed.** Done: XML escaping, `use_doc_ids` option, `indent`/`ensure_ascii` for JSON, nested metadata rendered as JSON. Not done: replacing the two lambdas in `_build_blocks` with a simpler structure.

- The `id` shown in XML, Markdown and JSON output is the 1-based position, not `doc.id`. For RAG prompts the real id (or a `source`) is usually what the model should cite. Add an `id_mode`/`include_ids` option, or at least document the difference prominently, since `Document.id` exists and the key is also called `id`.
- XML output does not escape content or metadata. A document containing `</document>` closes the block early, which is a prompt-structure injection vector for LLM prompts. Escape, or use a CDATA-like scheme, or document that content is inserted verbatim.
- `format_documents_as_json` is not a "concatenation" and uses `indent=2` unconditionally. Add `indent` and `ensure_ascii=False` parameters, since non-ASCII text is common in corpora.
- `_build_blocks` takes two lambdas for what is a two-element strategy. A small dataclass or two private functions per format would read more simply. Not urgent.
- Metadata values are stringified with `f"{value}"`. Nested values (lists and dicts) render as Python reprs, not as JSON.

### 2.6 Stats API shape

**Status: partly fixed.** Done: shared `ContentStatsBase`, `init=False` private state, public `bloom=` argument. Not done: typed result objects, one key set for both variants, `merge()`.

- `compute_content_stats_exact` and `compute_content_stats_approx` return untyped `dict[str, Any]`, and the printers depend on dict keys (`"p50_chars"` versus `"p50_chars_approx"`, `"duplicate_count"` versus `"approx_duplicate_count"`) plus boolean flags that mean "which dict is this".
  - Return a dataclass (or `TypedDict`) with the same field names, and have `to_dict()` for serialization. The printers then take the typed object.
  - Use one key set for both (`p50_chars`, `duplicate_count`) plus `is_exact`, so the printer does not need `p_suffix` and `dup_key` plumbing (`content_print.py:1065-1067`).
- `ExactContentStats` and `ApproxContentStats` duplicate about 80 lines (`update` prologue, `_percentile`, extremes tracking, a large part of the docstrings). Extract a shared `_ContentStatsBase` that handles counters and extremes, and let subclasses add the duplicate and percentile strategy.
- `_bloom`, `_reservoir` and `_seen_for_reservoir` are dataclass fields, so they appear in `__init__` (`ApproxContentStats(_bloom=...)`) and `_seen_hashes`/`_lengths` in `ExactContentStats` can be passed positionally. Use `field(init=False)` for private state.
- Stats classes have no `merge()`. A `merge(other)` would allow parallel or sharded computation (multiprocessing, per-file) and is cheap to add for counters, extremes and sets. A Bloom filter merge and a reservoir merge are well-defined too.

### 2.7 Exposing `MetadataMode` and the factories

**Status: fixed.** `MetadataMode` is exported; constants moved to `store/_constants.py` (public names `CONTENT_KEY`, `METADATA_KEY`). The `store.factory` package is still not re-exported from `docculus.store`.

`MetadataMode` is in `store.document.__all__` but not re-exported from `docculus.store`. The `store.factory` package is not mentioned by `store/__init__.py`. `store/custom.py` imports the private `_CONTENT_KEY` and `_METADATA_KEY` from `store/document.py`. Make them public constants in a small `store/_constants.py`.

### 2.8 Five near-identical store classes and five near-identical factories

**Status: not done** (cleanup, not a bug).

`store/custom.py` and `store/factory/custom.py` differ only by backend class, `metadata_schema` and `metadata_mode`. Consider:

- A single private helper `_typed_value_schema(metadata_schema)` and `_single_value_schema()`.
- A generic `StoreFactory(cls, **kwargs)` with thin aliases kept for discoverability, or a `functools.partial`-based factory.
- `_get_repr_kwargs` and `check_persista()` repeated in each factory.

The aim is to reduce the surface a new backend (e.g. Postgres) has to copy. This is a cleanup, not a bug.

### 2.9 `BaseDocumentStore` details

**Status: partly fixed.** Done: `Iterator` annotation, `items()`, `__contains__`. Deliberately not added: `__len__`/`__iter__` (an empty store would be falsy; key vs. document iteration is ambiguous). Not done: a shared contract test that checks the "raises until opened" behaviour for every backend.

- `iter_batches` is annotated `Generator[list[Document]]` with one type argument. That needs Python 3.13 typing defaults; for `requires-python >=3.11`, type checkers on older versions can complain. Use `Iterator[list[Document]]` (simpler, and what callers rely on).
- `keys()` is abstract, while `values()` has a default built on `iter_batches`. An `items()` (id and document) and `__len__`/`__contains__`/`__iter__` would make the class feel like a mapping, and `__contains__` is a one-liner over `contains`.
- The "raises until opened" contract is documented in the base class but not enforced there. Test it for every concrete class, since a test helper over `BaseDocumentStore` can verify the contract once for all backends.

### 2.10 Reservoir sampling is non-reproducible

**Status: fixed.** Private `random.Random` with a `seed` argument.

`analysis/content_approx.py:215` uses the global `random` module. Two runs over the same corpus give different percentiles, and unrelated code that calls `random.seed()` changes the results. Accept a `seed: int | None` or `rng: random.Random` and use a private `random.Random` instance.

### 2.11 Exact and approximate std-dev and mean

**Status: fixed.** Mean and standard deviation are exact (Welford); only percentiles are estimated.

The approximate class estimates the standard deviation from the reservoir, although mean and variance can be computed exactly in O(1) memory with Welford's algorithm. Do that, and mark only the percentiles as approximate (`std_dev_chars` would then be exact, which is better than the current docstring suggests).

## 3. Performance and memory

**Status of each bullet below is given in brackets at its end.**

- `ExactContentStats` docstring says lengths cost "8 bytes each". A Python `list[int]` costs about 8 bytes for the pointer plus about 28 bytes per distinct int object, so roughly 36 bytes each, and 100M docs is closer to 3.5 GB, not 800 MB. Store lengths in an `array.array("q")` (really 8 bytes each) or fix the docstring. Content hashes in a `set[bytes]` also cost about 33 bytes of payload plus about 50+ bytes of set overhead, so the "32 bytes each" figure is similarly optimistic. **[Done: docstring fixed, lengths already an `array`, hash set cost documented.]**
- `hashlib.sha256` over every document's full text is computed separately in `dedup.py`, `content_exact.py` and `content_approx.py`. A shared `_content_hash(content)` helper removes the repetition and lets you swap in a faster hash (`blake2b(digest_size=16)` is about 2x faster, and 16 bytes is plenty for dedup). That halves the memory for `_seen_hashes` too. **[Done: shared `content_hash` using 16-byte BLAKE2b.]**
- `to_dict()` in the exact stats sorts the full length list on every call. The docstring promises it is safe to call at any point, so repeated calls during streaming are O(n log n) each. Cache the sorted list until the next `update`, or compute all three percentiles in one pass (`statistics.quantiles`, or `heapq`/`numpy` where available). **[Done: sorted lengths cached until the next `update`.]**
- `_percentile` uses `round()`, which applies banker's rounding in Python, so `round(0.5)` is 0 and `round(1.5)` is 2. For p50 over an even-length sample this makes the median depend on parity. Either use linear interpolation (matches `numpy.percentile`/`statistics.quantiles`) or document the nearest-rank definition precisely. Users comparing against pandas will see different numbers. **[Done: nearest-rank with round-half-up, documented; percentile values over even-sized data changed.]**
- `DocumentStore.filter` could stream and short-circuit when no filters are given. For the empty-filter case, `iter_batches()` is the intended spelling anyway. **[Not done: the empty-filter case already works; a streaming return type would change the API.]**
- `get_lengths_with_ids(sort=True)` sorts the whole list when callers often need only the top-k. Offer `get_longest_documents(n)` or a `heapq.nlargest` path. Related: `get_shortest_document` and `get_longest_document` each iterate separately; a combined one-pass `get_length_extremes` would help. **[Not done: would add public API (top-k and combined extremes).]**

## 4. Documentation accuracy

- `analysis/content_print.py:1014-1033` documents a "schematic length-distribution bar chart" and a `_build_bar_chart_items` builder that does not exist in the module. The docstring is stale. Also `console: ... A new one is created via Console() if not provided` is wrong, since `get_console()` is used.
- `analysis/metadata_print.py:1519`: the docstring says keys are "read defensively via `[...]`/`.get(...)`, so a partial dict ... renders correctly", but `_build_summary_table` uses `stats["avg_keys"]`, `["min_keys"]`, `["max_keys"]` and `["missing_metadata_count"]` directly, so a partial dict raises `KeyError`. Fix either the code or the docstring. Also note `min_keys` and `max_keys` are `None` for empty input and `str(None)` is printed.
- `examples/document_report.py:1` has the module docstring "Generate synthetic LangChain Documents for testing and demos", which describes `fake.py` and not this script.
- `hashing/hasher.py`: `register_document_hasher()` runs as an import side effect. This is reasonable, but document that `hash_documents` and coola's `hash_object` only know about `Document` after `docculus.hashing` has been imported.
- `transform/id.py`: the `.. note::` block is reST syntax in a Markdown/mkdocstrings project that uses Google-style docstrings everywhere else. Use `Note:`.
- `utils/fake.py`: the "Returns" section is indented as if the description were a sub-item. Also, `Faker.seed()` being process-global is documented but could be avoided by `fake = faker.Faker(); fake.seed_instance(seed)`, which seeds only the local instance. That removes the Warning entirely.
- `get_lengths_with_ids` docstring example for `sort=True` produces the same output as the unsorted call, so it demonstrates nothing. Use an input in non-sorted order.
- README (262 lines) and `docs/docs/index.md` (204 lines) appear to overlap heavily. Use `mkdocs-include-markdown-plugin` (already a dev dependency) to include one from the other so they cannot drift.
- `store/custom.py` module docstring says "backed by `persista` SQLite stores", but it also contains DuckDB and in-memory stores.
- `testing/__init__.py` and the `testing.md` guide: say explicitly that `docculus.testing.fixtures` imports `pytest` at module import time and `pytest` is not in any extra.

## 5. Packaging, tests and tooling

### 5.1 Packaging

- `pyproject.toml` still has `[tool.uv.pip] torch-backend = "auto"`, which is a template leftover and unrelated to this package. Remove it.
- Classifiers list only POSIX and macOS; if Windows works (nothing here is platform-specific), add it, or state why not.
- `faker >=40.0,<41.0` is a very tight upper bound for an optional test-data dependency; this blocks users on Faker 41+ with no benefit. Relax to `<50` or drop the cap.
- `rich` is a hard requirement for `display` and the `print_*_report` functions but is only an optional extra. The error comes from `check_rich()` at call time, which is fine, but add `rich` to the install instructions for the `display` module in the README, since `import docculus.display` succeeds and then fails on first use.
- There is no `all` extra written in `pyproject.toml` (the `autoextras` hook presumably generates it); check that `pip install docculus[all]` in the docs matches what the built wheel provides.
- `version = "0.0.1"` is static while `__init__.py` reads the installed metadata version. Fine, but make sure the release workflow bumps both from a single source.

### 5.2 Tests

- Doctests: `ci-doctest.yaml` exists, but `copy_ids_to_metadata`'s example (1.4) and some examples in `analysis` would fail if executed as written. Verify the workflow runs against `src/` with the same runner as the local `make` target.
- Add property-based tests (Hypothesis) for `deterministic id`/`hash` stability under metadata key order, for the exact-versus-approx stats agreement on counts, and for the store round trip (`set_many` then `get`) across all five store classes and both metadata modes. The store tests in `tests/unit/store/test_document.py` (713 lines) and `test_custom.py` (591 lines) are long; a parametrized contract test run against every backend would shrink them and catch backend divergence (see 1.5).
- `tests/integration/` contains only `utils`. Add integration tests that run the full pipeline: load documents, `assign_ids`, `deduplicate_documents`, store round trip, stats report. `examples/document_report.py` could double as a smoke test.
- There is no test for the Rich markup issue (1.1). Add a regression test that prints a document whose metadata contains `[/x]` and `[bold]`.
- `__pycache__` directories show up under `tests/`; confirm they are gitignored (the `.gitignore` is 218 lines, so probably yes).

### 5.3 CI, vendoring and housekeeping

- 32 workflow files is a lot for a small library. `lib-*`, `bot-*` and `nightly-*` look shared across the author's other repos. If they are synced by `bot-sync-shared-makefile.yaml`, state that in `CONTRIBUTING`/`.github/GUIDELINES.md`, so contributors know not to edit them here.
- `CODE_OF_CONDUCT.md` is duplicated in the repo root and in `.make/`, and `LICENSE` is as well. Harmless, but the sync job should be the only writer.
- Add a `CHANGELOG.md` or lean on GitHub Releases explicitly (the `Changelog` URL already points there). Either way, breaking changes like 1.2 need a visible note.
- Consider enabling `ty`/`mypy` strictness for the `store` package, where the `persista` types are conditionally imported (`if is_persista_available()`). A `TYPE_CHECKING` import of those names would let the type checker see them without runtime coupling.

## 6. Smaller code-level cleanups

- `utils/imports/faker.py` and `persista.py` are copies of each other with the name replaced. A small factory (`make_import_helpers("faker")`) would remove the duplication and make adding `duckdb` and `rich` helpers (currently there is no `check_duckdb`) trivial. The `faker_available` decorator names in `utils/imports` and in `testing/fixtures` are different things (a run-or-skip decorator versus a pytest `skipif` marker) with the same name; rename one (e.g. `skip_if_no_faker`) to avoid mixed-up imports.
- `document/length.py`: `get_shortest_document` and `get_longest_document` are the same loop with `<`/`>`. Share one `_extreme_document(documents, better, ...)`.
- `document/length.py`: `get_lengths_with_ids` returns `list[tuple[Any, int]]`; the id type is `str | None`, so use that rather than `Any`. The same goes for `find_duplicate_document_ids` and `find_empty_document_ids` (`list[Any]`).
- `display/document.py`: the 0.8 threshold in `_truncate` is a magic number; make it a named constant. The word-boundary snap also only handles spaces, not newlines or CJK text (no spaces, so it always hard-cuts, which is fine, but worth a comment).
- `display/metadata.py`: `print_documents_metadata` takes a `Sequence` only to call `len()` for the title. It would work with any iterable by counting while building lines.
- `analysis/metadata_stats.py:1685`: `value == ""` can return an array for numpy-valued metadata and raise on truthiness. Guard with `isinstance(value, str) and value == ""`.
- `analysis/metadata_stats.py`: `_key_values_truncated` and `_key_values` are keyed identically with the per-key counters; one small `_KeyStats` dataclass per key would replace five parallel dicts and make `update` shorter.
- `validation/consistency.py`: it logs a warning per inconsistent document and returns `False`. Returning the list of offending ids (or a small result object) would be more useful than a bare bool, and `raise_error=True` could then list all of them instead of failing on the first one.
- `transform/dedup.py`: dedup is keyed on `(id, content, metadata)` while `analysis.find_duplicate_document_ids` is keyed on content only. Both are reasonable, but the names suggest the same concept. Cross-link them in the docstrings, and consider a `deduplicate_documents(..., by="content" | "id" | "all")` option, because content-only dedup is the common need in RAG pipelines.
- `transform/filter.py`: `filter_by_metadata_values` takes `set[Any]`; accept any `Collection` and convert internally, and handle unhashable metadata values (currently `TypeError` from `in set`). `filter_by_metadata_range` should raise a clear `ValueError` if `lower > upper`.
- `hashing/hasher.py`: `DocumentHasher.hash` ignores `ignore_unhashable`. That is fine, but it will still raise on non-JSON metadata (see 1.2), which is exactly the case the flag is meant for.
- `examples/`: only one example, and it needs `faker` and `rich`. Add a second that uses a store and a deduplication step.

## 7. Feature ideas (optional)

- A `Pipeline`/`compose` helper, or at least documented chaining patterns, for `assign_ids`, `deduplicate_documents`, `filter_*` and `truncate_documents`.
- Analysis directly over a store: `compute_content_stats_exact(store.values())` already works, but a documented recipe and a `store.stats()` shortcut would make the store and analysis halves of the library feel connected.
- Token-length statistics (optional `tiktoken` extra), since character counts are a weak proxy for context-window planning.
- Near-duplicate detection (MinHash/SimHash) beyond the exact and Bloom-filter content matching.
- Chunk-aware helpers: validating that chunks reference an existing parent via the `source_id` metadata that `copy_ids_to_metadata` writes.
- JSON/CSV export of the stats reports, so they can be logged in CI instead of only printed.

## Suggested order of work

1. 1.1 (markup escaping), 1.3 (`sort_by_metadata` naming), 1.4 (doctest), 1.6 (dedup surrogate handling): small, low risk.
2. 1.2 (hash format change) together with a changelog note, while the version is still 0.0.x.
3. 1.5 (store flat-mode contract) with a parametrized contract test across backends.
4. 2.1 to 2.4 (type and signature consistency), which are mostly mechanical.
5. 2.6 and 3 (stats refactor, typed results, memory fixes) as one change.
6. Documentation fixes in section 4 and the packaging cleanups in 5.1.
