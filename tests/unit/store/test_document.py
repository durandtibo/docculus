from __future__ import annotations

from collections.abc import Generator, Iterator

import pytest
from langchain_core.documents import Document

from docculus.store.document import DocumentStore, MetadataMode
from docculus.testing.fixtures import persista_available
from docculus.utils.imports import is_persista_available

if is_persista_available():
    from persista.store import BaseStore, InMemoryStore, SQLiteStore

pytest.importorskip("persista")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _new_raw_store(store_cls: type[BaseStore]) -> BaseStore:
    if store_cls is SQLiteStore:
        return SQLiteStore(":memory:")
    return store_cls()


@pytest.fixture(params=[InMemoryStore, SQLiteStore], ids=["in_memory", "sqlite"])
def raw_store_cls(request: pytest.FixtureRequest) -> type[BaseStore]:
    return request.param


@pytest.fixture(params=["flat", "single"])
def metadata_mode(request: pytest.FixtureRequest) -> MetadataMode:
    return request.param


@pytest.fixture
def store(
    raw_store_cls: type[BaseStore], metadata_mode: MetadataMode
) -> Generator[DocumentStore, None, None]:
    with DocumentStore(_new_raw_store(raw_store_cls), metadata_mode=metadata_mode) as store:
        yield store


@pytest.fixture
def docs() -> list[Document]:
    return [
        Document(
            id="1",
            page_content="Intro to Python",
            metadata={"author": "Alice", "category": "Programming"},
        ),
        Document(
            id="2",
            page_content="Advanced Python",
            metadata={"author": "Alice", "category": "Programming"},
        ),
        Document(
            id="3",
            page_content="History of Rome",
            metadata={"author": "Bob", "category": "History"},
        ),
        Document(
            id="4",
            page_content="History of Greece",
            metadata={"author": "Bob", "category": "History"},
        ),
    ]


###############################
#     Tests for DocumentStore #
###############################


# --- constructor ---


@persista_available
def test_init_store_returns_underlying_store(raw_store_cls: type[BaseStore]) -> None:
    raw_store = _new_raw_store(raw_store_cls)
    with DocumentStore(raw_store) as store:
        assert store.store is raw_store


@persista_available
def test_init_metadata_mode_default_is_flat(raw_store_cls: type[BaseStore]) -> None:
    with DocumentStore(_new_raw_store(raw_store_cls)) as store:
        assert store.metadata_mode == "flat"


@persista_available
def test_init_metadata_mode_is_stored(store: DocumentStore, metadata_mode: MetadataMode) -> None:
    assert store.metadata_mode == metadata_mode


@persista_available
def test_init_invalid_metadata_mode_raises(raw_store_cls: type[BaseStore]) -> None:
    with (
        _new_raw_store(raw_store_cls) as raw_store,
        pytest.raises(ValueError, match=r"Incorrect metadata_mode"),
    ):
        DocumentStore(raw_store, metadata_mode="bogus")


# --- open ---


@persista_available
def test_open_makes_store_usable(raw_store_cls: type[BaseStore]) -> None:
    doc_store = DocumentStore(_new_raw_store(raw_store_cls))
    doc_store.open()
    try:
        doc_store.set_many([Document(id="1", page_content="hello", metadata={})])
        assert doc_store.count() == 1
    finally:
        doc_store.close()


@persista_available
def test_open_is_idempotent(raw_store_cls: type[BaseStore]) -> None:
    doc_store = DocumentStore(_new_raw_store(raw_store_cls))
    doc_store.open()
    doc_store.open()  # should not raise
    doc_store.close()


# --- aopen ---


@persista_available
async def test_aopen_makes_store_usable(raw_store_cls: type[BaseStore]) -> None:
    doc_store = DocumentStore(_new_raw_store(raw_store_cls))
    await doc_store.aopen()
    try:
        await doc_store.aset_many([Document(id="1", page_content="hello", metadata={})])
        assert await doc_store.acount() == 1
    finally:
        await doc_store.aclose()


@persista_available
async def test_aopen_is_idempotent(raw_store_cls: type[BaseStore]) -> None:
    doc_store = DocumentStore(_new_raw_store(raw_store_cls))
    await doc_store.aopen()
    await doc_store.aopen()  # should not raise
    await doc_store.aclose()


# --- set_many ---


@persista_available
def test_set_many_increases_count(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert store.count() == len(docs)


@persista_available
def test_set_many_empty_is_no_op(store: DocumentStore) -> None:
    store.set_many([])
    assert store.count() == 0


@persista_available
def test_set_many_overwrites_existing(store: DocumentStore) -> None:
    store.set_many([Document(id="1", page_content="original", metadata={"a": 1})])
    store.set_many([Document(id="1", page_content="updated", metadata={"a": 2})])
    assert store.count() == 1
    assert store.get("1").page_content == "updated"
    assert store.get("1").metadata == {"a": 2}


@persista_available
def test_set_many_document_without_id_raises(store: DocumentStore) -> None:
    with pytest.raises(ValueError, match=r"Document must have an 'id'"):
        store.set_many([Document(page_content="no id")])


@persista_available
def test_set_many_flat_mode_stores_metadata_top_level(raw_store_cls: type[BaseStore]) -> None:
    raw_store = _new_raw_store(raw_store_cls)
    with DocumentStore(raw_store, metadata_mode="flat") as store:
        store.set_many([Document(id="1", page_content="hello", metadata={"author": "Alice"})])
        assert raw_store.get("1") == {"page_content": "hello", "author": "Alice"}


@persista_available
def test_set_many_single_mode_stores_metadata_nested(raw_store_cls: type[BaseStore]) -> None:
    raw_store = _new_raw_store(raw_store_cls)
    with DocumentStore(raw_store, metadata_mode="single") as store:
        store.set_many([Document(id="1", page_content="hello", metadata={"author": "Alice"})])
        assert raw_store.get("1") == {
            "page_content": "hello",
            "metadata": {"author": "Alice"},
        }


# --- get ---


@persista_available
def test_get_existing_document(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert store.get("1") == Document(
        id="1",
        page_content="Intro to Python",
        metadata={"author": "Alice", "category": "Programming"},
    )
    assert store.get("2") == Document(
        id="2",
        page_content="Advanced Python",
        metadata={"author": "Alice", "category": "Programming"},
    )
    assert store.get("3") == Document(
        id="3",
        page_content="History of Rome",
        metadata={"author": "Bob", "category": "History"},
    )
    assert store.get("4") == Document(
        id="4",
        page_content="History of Greece",
        metadata={"author": "Bob", "category": "History"},
    )


@persista_available
def test_get_missing_id_returns_none(store: DocumentStore) -> None:
    assert store.get("nonexistent") is None


# --- get_many ---


@persista_available
def test_get_many_returns_correct_length(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert len(store.get_many(["1", "2", "99"])) == 3


@persista_available
def test_get_many_returns_none_for_missing(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    result = store.get_many(["1", "99", "2"])
    assert result[1] is None


@persista_available
def test_get_many_preserves_order(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    result = store.get_many(["3", "1", "2"])
    assert [doc.id for doc in result] == ["3", "1", "2"]


@persista_available
def test_get_many_empty_list_returns_empty_list(store: DocumentStore) -> None:
    assert store.get_many([]) == []


# --- filter ---


@persista_available
def test_filter_no_args_returns_all(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert len(store.filter()) == len(docs)


@persista_available
def test_filter_single_field(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    result = store.filter(author="Alice")
    assert len(result) == 2
    assert all(doc.metadata["author"] == "Alice" for doc in result)


@persista_available
def test_filter_multiple_fields(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    result = store.filter(author="Alice", category="Programming")
    assert len(result) == 2


@persista_available
def test_filter_no_match_returns_empty(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert store.filter(author="Charlie") == []


@persista_available
def test_filter_empty_store_returns_empty(store: DocumentStore) -> None:
    assert store.filter(author="Alice") == []


# --- delete ---


@persista_available
def test_delete_removes_document(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    store.delete("1")
    assert store.count() == len(docs) - 1
    assert store.get("1") is None


@persista_available
def test_delete_nonexistent_is_silent(store: DocumentStore) -> None:
    store.delete("nonexistent")


# --- delete_many ---


@persista_available
def test_delete_many_removes_documents(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    store.delete_many(["1", "3"])
    assert store.count() == len(docs) - 2
    assert store.get("1") is None
    assert store.get("3") is None


@persista_available
def test_delete_many_preserves_other_documents(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    store.delete_many(["1", "3"])
    assert store.get("2") is not None
    assert store.get("4") is not None


@persista_available
def test_delete_many_empty_list_is_no_op(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    store.delete_many([])
    assert store.count() == len(docs)


@persista_available
def test_delete_many_nonexistent_ids_are_silent(store: DocumentStore) -> None:
    store.delete_many(["99", "100"])


# --- clear ---


@persista_available
def test_clear_removes_all_documents(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    store.clear()
    assert store.count() == 0
    assert list(store.keys()) == []


@persista_available
def test_clear_empty_store_is_no_op(store: DocumentStore) -> None:
    store.clear()
    assert store.count() == 0


# --- contains ---


@persista_available
def test_contains_true_when_id_present(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert store.contains("1")


@persista_available
def test_contains_false_when_id_missing(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert not store.contains("99")


@persista_available
def test_contains_false_when_store_empty(store: DocumentStore) -> None:
    assert not store.contains("1")


# --- contains_many ---


@persista_available
def test_contains_many_mixed(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert store.contains_many(["1", "99", "3", "42"]) == [True, False, True, False]


@persista_available
def test_contains_many_empty_input_returns_empty_list(store: DocumentStore) -> None:
    assert store.contains_many([]) == []


# --- keys ---


@persista_available
def test_keys_empty_store_yields_nothing(store: DocumentStore) -> None:
    assert list(store.keys()) == []


@persista_available
def test_keys_returns_all_ids(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert sorted(store.keys()) == sorted(str(doc.id) for doc in docs)


# --- iter_batches ---


@persista_available
def test_iter_batches_empty_store_yields_nothing(store: DocumentStore) -> None:
    assert list(store.iter_batches()) == []


@persista_available
def test_iter_batches_returns_generator(store: DocumentStore) -> None:
    assert isinstance(store.iter_batches(), Iterator)


@persista_available
def test_iter_batches_yields_correct_batch_sizes(
    store: DocumentStore, docs: list[Document]
) -> None:
    store.set_many(docs)
    batches = list(store.iter_batches(batch_size=2))
    assert [len(batch) for batch in batches] == [2, 2]


@persista_available
def test_iter_batches_returns_all_documents(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    result: dict[str, Document] = {}
    for batch in store.iter_batches(batch_size=2):
        result.update({doc.id: doc for doc in batch})
    assert sorted(result.keys()) == sorted(str(doc.id) for doc in docs)


# --- values ---


@persista_available
def test_values_returns_all_documents(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    result = list(store.values())
    assert sorted(str(doc.id) for doc in result) == sorted(str(doc.id) for doc in docs)


# --- avalues ---


@persista_available
async def test_avalues_returns_all_documents(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    result = [doc async for doc in store.avalues()]
    assert sorted(str(doc.id) for doc in result) == sorted(str(doc.id) for doc in docs)


@persista_available
async def test_avalues_empty_store_yields_nothing(store: DocumentStore) -> None:
    assert [doc async for doc in store.avalues()] == []


# --- count ---


@persista_available
def test_count_empty_store(store: DocumentStore) -> None:
    assert store.count() == 0


@persista_available
def test_count_after_set_many(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert store.count() == len(docs)


# --- close / closed ---


@persista_available
def test_closed_false_before_close(store: DocumentStore) -> None:
    assert not store.closed


@persista_available
def test_closed_true_after_close(store: DocumentStore) -> None:
    store.close()
    assert store.closed


@persista_available
def test_close_is_idempotent(store: DocumentStore) -> None:
    store.close()
    store.close()  # should not raise


# --- context manager ---


@persista_available
def test_context_manager_returns_self(store: DocumentStore) -> None:
    assert isinstance(store, DocumentStore)


@persista_available
def test_context_manager_closes_on_normal_exit(raw_store_cls: type[BaseStore]) -> None:
    with DocumentStore(_new_raw_store(raw_store_cls)) as store:
        store.set_many([Document(id="1", page_content="hello", metadata={})])
        assert store.count() == 1
    assert store.closed


@persista_available
def test_context_manager_closes_on_exception(raw_store_cls: type[BaseStore]) -> None:
    msg = "boom"
    with (
        pytest.raises(ValueError, match="boom"),
        DocumentStore(_new_raw_store(raw_store_cls)) as store,
    ):
        raise ValueError(msg)
    assert store.closed


# ---------------------------------------------------------------------------
# Async methods
# ---------------------------------------------------------------------------


# --- async context manager ---


@persista_available
async def test_async_context_manager_returns_self(raw_store_cls: type[BaseStore]) -> None:
    doc_store = DocumentStore(_new_raw_store(raw_store_cls))
    async with doc_store as store:
        assert store is doc_store


@persista_available
async def test_async_context_manager_closes_on_normal_exit(
    raw_store_cls: type[BaseStore],
) -> None:
    async with DocumentStore(_new_raw_store(raw_store_cls)) as store:
        await store.aset_many([Document(id="1", page_content="hello", metadata={})])
        assert await store.acount() == 1
    assert store.closed


@persista_available
async def test_async_context_manager_closes_on_exception(raw_store_cls: type[BaseStore]) -> None:
    msg = "boom"
    doc_store = DocumentStore(_new_raw_store(raw_store_cls))
    with pytest.raises(ValueError, match="boom"):
        async with doc_store:
            raise ValueError(msg)
    assert doc_store.closed


# --- aset_many / aget / aget_many ---


@persista_available
async def test_aset_many_and_aget(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    result = await store.aget("1")
    assert result.id == "1"
    assert result.page_content == docs[0].page_content
    assert result.metadata == docs[0].metadata
    assert await store.aget("missing") is None


@persista_available
async def test_aget_many(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    result = await store.aget_many(["1", "99", "2"])
    assert result[1] is None
    assert [doc.id for doc in result if doc is not None] == ["1", "2"]


# --- afilter ---


@persista_available
async def test_afilter_single_field(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    result = await store.afilter(author="Bob")
    assert len(result) == 2
    assert all(doc.metadata["author"] == "Bob" for doc in result)


@persista_available
async def test_afilter_no_match_returns_empty(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    assert await store.afilter(author="Charlie") == []


# --- adelete / adelete_many ---


@persista_available
async def test_adelete_removes_document(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    await store.adelete("1")
    assert await store.acount() == len(docs) - 1
    assert await store.aget("1") is None


@persista_available
async def test_adelete_nonexistent_is_silent(store: DocumentStore) -> None:
    await store.adelete("nonexistent")


@persista_available
async def test_adelete_many_preserves_other_documents(
    store: DocumentStore, docs: list[Document]
) -> None:
    await store.aset_many(docs)
    await store.adelete_many(["1", "3"])
    assert await store.aget("2") is not None
    assert await store.aget("4") is not None


# --- aclear ---


@persista_available
async def test_aclear_removes_all_documents(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    await store.aclear()
    assert await store.acount() == 0


# --- acontains / acontains_many ---


@persista_available
async def test_acontains(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    assert await store.acontains("1") is True
    assert await store.acontains("99") is False


@persista_available
async def test_acontains_many(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    assert await store.acontains_many(["1", "99"]) == [True, False]


# --- akeys / aiter_batches ---


@persista_available
async def test_akeys_returns_all_ids(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    assert sorted([doc_id async for doc_id in store.akeys()]) == sorted(str(doc.id) for doc in docs)


@persista_available
async def test_akeys_empty_store_yields_nothing(store: DocumentStore) -> None:
    assert [doc_id async for doc_id in store.akeys()] == []


@persista_available
async def test_aiter_batches_returns_all_documents(
    store: DocumentStore, docs: list[Document]
) -> None:
    await store.aset_many(docs)
    result: dict[str, Document] = {}
    async for batch in store.aiter_batches(batch_size=2):
        result.update({doc.id: doc for doc in batch})
    assert sorted(result.keys()) == sorted(str(doc.id) for doc in docs)


@persista_available
async def test_aiter_batches_empty_store_yields_nothing(store: DocumentStore) -> None:
    assert [batch async for batch in store.aiter_batches()] == []


# --- acount ---


@persista_available
async def test_acount_empty_store(store: DocumentStore) -> None:
    assert await store.acount() == 0


@persista_available
async def test_acount_after_aset_many(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    assert await store.acount() == len(docs)


# --- aclose ---


@persista_available
async def test_aclose_is_idempotent(store: DocumentStore) -> None:
    await store.aclose()
    await store.aclose()
    assert store.closed
