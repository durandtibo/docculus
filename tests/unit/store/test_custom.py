from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from langchain_core.documents import Document

from docculus.store.custom import (
    DuckDBDocumentStore,
    InMemoryDocumentStore,
    SQLiteDocumentStore,
    TypedDuckDBDocumentStore,
    TypedSQLiteDocumentStore,
)
from docculus.testing.fixtures import persista_available
from docculus.utils.imports import is_persista_available

if is_persista_available():
    from persista.utils.imports import is_duckdb_available


if TYPE_CHECKING:
    from docculus.store.document import DocumentStore

pytest.importorskip("persista")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_STORE_FACTORIES = {
    "in_memory": lambda: InMemoryDocumentStore(),
    "sqlite": lambda: SQLiteDocumentStore(),
    "typed_sqlite": lambda: TypedSQLiteDocumentStore(metadata_schema={"author": "TEXT"}),
}
if is_duckdb_available():
    _STORE_FACTORIES |= {
        "duckdb": lambda: DuckDBDocumentStore(),
        "typed_duckdb": lambda: TypedDuckDBDocumentStore(metadata_schema={"author": "TEXT"}),
    }


@pytest.fixture(params=list(_STORE_FACTORIES), ids=list(_STORE_FACTORIES))
def store_cls(request: pytest.FixtureRequest) -> str:
    """Identify which custom document store implementation to exercise,
    so every test below runs once per implementation."""
    return request.param


def _new_document_store(name: str) -> DocumentStore:
    return _STORE_FACTORIES[name]()


@pytest.fixture
def store(store_cls: str):  # noqa: ANN201
    with _new_document_store(store_cls) as store:
        yield store


@pytest.fixture
def docs() -> list[Document]:
    return [
        Document(
            id="1",
            page_content="Intro to Python",
            metadata={"author": "Alice"},
        ),
        Document(
            id="2",
            page_content="Advanced Python",
            metadata={"author": "Alice"},
        ),
        Document(
            id="3",
            page_content="History of Rome",
            metadata={"author": "Bob"},
        ),
    ]


###############################################################################
#     Consistency tests: shared behavior across custom implementations      #
###############################################################################


# --- construction ---


@persista_available
def test_default_database_is_in_memory(store_cls: str) -> None:
    with _new_document_store(store_cls) as store:
        assert not store.closed


# --- set_many / get ---


@persista_available
def test_set_many_and_get_roundtrip(store: DocumentStore) -> None:
    store.set_many([Document(id="1", page_content="hello", metadata={"author": "Alice"})])
    doc = store.get("1")
    assert doc == Document(id="1", page_content="hello", metadata={"author": "Alice"})


@persista_available
def test_set_many_increases_count(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert store.count() == len(docs)


@persista_available
def test_set_many_overwrites_existing(store: DocumentStore) -> None:
    store.set_many([Document(id="1", page_content="original", metadata={"author": "Alice"})])
    store.set_many([Document(id="1", page_content="updated", metadata={"author": "Bob"})])
    assert store.count() == 1
    updated = store.get("1")
    assert updated.page_content == "updated"
    assert updated.metadata == {"author": "Bob"}


@persista_available
def test_set_many_document_without_id_raises(store: DocumentStore) -> None:
    with pytest.raises(ValueError, match=r"Document must have an 'id'"):
        store.set_many([Document(page_content="no id")])


@persista_available
def test_get_missing_id_returns_none(store: DocumentStore) -> None:
    assert store.get("missing") is None


# --- get_many ---


@persista_available
def test_get_many_preserves_order_and_missing(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    result = store.get_many(["3", "missing", "1"])
    assert [doc.id if doc is not None else None for doc in result] == ["3", None, "1"]


# --- filter ---


@persista_available
def test_filter_by_metadata_field(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    result = store.filter(author="Alice")
    assert sorted(doc.id for doc in result) == ["1", "2"]


@persista_available
def test_filter_no_match_returns_empty(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert store.filter(author="Charlie") == []


# --- delete / delete_many ---


@persista_available
def test_delete_removes_document(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    store.delete("1")
    assert store.get("1") is None
    assert store.count() == len(docs) - 1


@persista_available
def test_delete_many_removes_documents(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    store.delete_many(["1", "3"])
    assert store.count() == len(docs) - 2
    assert store.get("2") is not None


# --- clear ---


@persista_available
def test_clear_removes_all_documents(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    store.clear()
    assert store.count() == 0


# --- contains / contains_many ---


@persista_available
def test_contains(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert store.contains("1")
    assert not store.contains("missing")


@persista_available
def test_contains_many(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert store.contains_many(["1", "missing", "3"]) == [True, False, True]


# --- keys / values / iter_batches ---


@persista_available
def test_keys_returns_all_ids(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    assert sorted(store.keys()) == sorted(str(doc.id) for doc in docs)


@persista_available
def test_iter_batches_returns_all_documents(store: DocumentStore, docs: list[Document]) -> None:
    store.set_many(docs)
    result: dict[str, Document] = {}
    for batch in store.iter_batches(batch_size=2):
        result.update({doc.id: doc for doc in batch})
    assert sorted(result.keys()) == sorted(str(doc.id) for doc in docs)


# --- count ---


@persista_available
def test_count_empty_store(store: DocumentStore) -> None:
    assert store.count() == 0


# --- open / close / context manager ---


@persista_available
def test_context_manager_opens_and_closes(store_cls: str) -> None:
    store = _new_document_store(store_cls)
    with store as opened:
        assert not opened.closed
    assert store.closed


@persista_available
def test_open_is_idempotent(store_cls: str) -> None:
    store = _new_document_store(store_cls)
    store.open()
    store.open()  # should not raise
    store.close()


@persista_available
def test_close_is_idempotent(store: DocumentStore) -> None:
    store.close()
    store.close()  # should not raise


###############################################################################
#     Async consistency tests                                               #
###############################################################################


# --- construction ---


@persista_available
async def test_adefault_database_is_in_memory(store_cls: str) -> None:
    store = _new_document_store(store_cls)
    async with store as opened:
        assert not opened.closed


# --- aset_many / aget ---


@persista_available
async def test_aset_many_and_aget_roundtrip(store: DocumentStore) -> None:
    await store.aset_many([Document(id="1", page_content="hello", metadata={"author": "Alice"})])
    doc = await store.aget("1")
    assert doc == Document(id="1", page_content="hello", metadata={"author": "Alice"})


@persista_available
async def test_aset_many_increases_count(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    assert await store.acount() == len(docs)


@persista_available
async def test_aset_many_overwrites_existing(store: DocumentStore) -> None:
    await store.aset_many([Document(id="1", page_content="original", metadata={"author": "Alice"})])
    await store.aset_many([Document(id="1", page_content="updated", metadata={"author": "Bob"})])
    assert await store.acount() == 1
    updated = await store.aget("1")
    assert updated.page_content == "updated"
    assert updated.metadata == {"author": "Bob"}


@persista_available
async def test_aset_many_document_without_id_raises(store: DocumentStore) -> None:
    with pytest.raises(ValueError, match=r"Document must have an 'id'"):
        await store.aset_many([Document(page_content="no id")])


@persista_available
async def test_aget_missing_id_returns_none(store: DocumentStore) -> None:
    assert await store.aget("missing") is None


# --- aget_many ---


@persista_available
async def test_aget_many_preserves_order_and_missing(
    store: DocumentStore, docs: list[Document]
) -> None:
    await store.aset_many(docs)
    result = await store.aget_many(["3", "missing", "1"])
    assert [doc.id if doc is not None else None for doc in result] == ["3", None, "1"]


# --- afilter ---


@persista_available
async def test_afilter_by_metadata_field(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    result = await store.afilter(author="Bob")
    assert [doc.id for doc in result] == ["3"]


@persista_available
async def test_afilter_no_match_returns_empty(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    assert await store.afilter(author="Charlie") == []


# --- adelete / adelete_many ---


@persista_available
async def test_adelete_removes_document(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    await store.adelete("1")
    assert await store.aget("1") is None
    assert await store.acount() == len(docs) - 1


@persista_available
async def test_adelete_many_removes_documents(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    await store.adelete_many(["1", "3"])
    assert await store.acount() == len(docs) - 2
    assert await store.aget("2") is not None


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
    assert await store.acontains("1")
    assert not await store.acontains("missing")


@persista_available
async def test_acontains_many(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    assert await store.acontains_many(["1", "missing", "3"]) == [True, False, True]


# --- akeys / aiter_batches ---


@persista_available
async def test_akeys_returns_all_ids(store: DocumentStore, docs: list[Document]) -> None:
    await store.aset_many(docs)
    assert sorted([doc_id async for doc_id in store.akeys()]) == sorted(str(doc.id) for doc in docs)


@persista_available
async def test_aiter_batches_returns_all_documents(
    store: DocumentStore, docs: list[Document]
) -> None:
    await store.aset_many(docs)
    result: dict[str, Document] = {}
    async for batch in store.aiter_batches(batch_size=2):
        result.update({doc.id: doc for doc in batch})
    assert sorted(result.keys()) == sorted(str(doc.id) for doc in docs)


# --- acount ---


@persista_available
async def test_acount_empty_store(store: DocumentStore) -> None:
    assert await store.acount() == 0


# --- aopen / aclose / async context manager ---


@persista_available
async def test_async_context_manager_opens_and_closes(store_cls: str) -> None:
    store = _new_document_store(store_cls)
    async with store as opened:
        assert not opened.closed
    assert store.closed


@persista_available
async def test_aopen_is_idempotent(store_cls: str) -> None:
    store = _new_document_store(store_cls)
    await store.aopen()
    await store.aopen()  # should not raise
    await store.aclose()


@persista_available
async def test_aclose_is_idempotent(store: DocumentStore) -> None:
    await store.aclose()
    await store.aclose()  # should not raise


###############################################################################
#     InMemoryDocumentStore-specific tests                                  #
###############################################################################


@persista_available
def test_in_memory_document_store_default_metadata_mode_is_flat() -> None:
    with InMemoryDocumentStore() as store:
        assert store.metadata_mode == "flat"


@persista_available
async def test_ain_memory_document_store_default_metadata_mode_is_flat() -> None:
    async with InMemoryDocumentStore() as store:
        assert store.metadata_mode == "flat"


###############################################################################
#     DuckDBDocumentStore-specific tests                                    #
###############################################################################


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_duckdb_document_store_default_metadata_mode_is_single() -> None:
    with DuckDBDocumentStore() as store:
        assert store.metadata_mode == "single"


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
async def test_aduckdb_document_store_default_metadata_mode_is_single() -> None:
    async with DuckDBDocumentStore() as store:
        assert store.metadata_mode == "single"


###############################################################################
#     TypedDuckDBDocumentStore-specific tests                               #
###############################################################################


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_typed_duckdb_document_store_default_metadata_mode_is_flat() -> None:
    with TypedDuckDBDocumentStore() as store:
        assert store.metadata_mode == "flat"


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
async def test_atyped_duckdb_document_store_default_metadata_mode_is_flat() -> None:
    async with TypedDuckDBDocumentStore() as store:
        assert store.metadata_mode == "flat"


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_typed_duckdb_document_store_without_metadata_schema() -> None:
    with TypedDuckDBDocumentStore() as store:
        store.set_many([Document(id="1", page_content="hello", metadata={})])
        assert store.get("1") == Document(id="1", page_content="hello", metadata={})


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
async def test_atyped_duckdb_document_store_without_metadata_schema() -> None:
    async with TypedDuckDBDocumentStore() as store:
        await store.aset_many([Document(id="1", page_content="hello", metadata={})])
        assert await store.aget("1") == Document(id="1", page_content="hello", metadata={})


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_typed_duckdb_document_store_with_metadata_schema() -> None:
    with TypedDuckDBDocumentStore(metadata_schema={"author": "TEXT"}) as store:
        store.set_many([Document(id="1", page_content="hello", metadata={"author": "Alice"})])
        assert store.get("1") == Document(
            id="1", page_content="hello", metadata={"author": "Alice"}
        )


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
async def test_atyped_duckdb_document_store_with_metadata_schema() -> None:
    async with TypedDuckDBDocumentStore(metadata_schema={"author": "TEXT"}) as store:
        await store.aset_many(
            [Document(id="1", page_content="hello", metadata={"author": "Alice"})]
        )
        assert await store.aget("1") == Document(
            id="1", page_content="hello", metadata={"author": "Alice"}
        )


###############################################################################
#     SQLiteDocumentStore-specific tests                                    #
###############################################################################


@persista_available
def test_sqlite_document_store_default_metadata_mode_is_single() -> None:
    with SQLiteDocumentStore() as store:
        assert store.metadata_mode == "single"


@persista_available
async def test_asqlite_document_store_default_metadata_mode_is_single() -> None:
    async with SQLiteDocumentStore() as store:
        assert store.metadata_mode == "single"


###############################################################################
#     TypedSQLiteDocumentStore-specific tests                               #
###############################################################################


@persista_available
def test_typed_sqlite_document_store_default_metadata_mode_is_flat() -> None:
    with TypedSQLiteDocumentStore() as store:
        assert store.metadata_mode == "flat"


@persista_available
async def test_atyped_sqlite_document_store_default_metadata_mode_is_flat() -> None:
    async with TypedSQLiteDocumentStore() as store:
        assert store.metadata_mode == "flat"


@persista_available
def test_typed_sqlite_document_store_without_metadata_schema() -> None:
    with TypedSQLiteDocumentStore() as store:
        store.set_many([Document(id="1", page_content="hello", metadata={})])
        assert store.get("1") == Document(id="1", page_content="hello", metadata={})


@persista_available
async def test_atyped_sqlite_document_store_without_metadata_schema() -> None:
    async with TypedSQLiteDocumentStore() as store:
        await store.aset_many([Document(id="1", page_content="hello", metadata={})])
        assert await store.aget("1") == Document(id="1", page_content="hello", metadata={})


@persista_available
def test_typed_sqlite_document_store_with_metadata_schema() -> None:
    with TypedSQLiteDocumentStore(metadata_schema={"author": "TEXT"}) as store:
        store.set_many([Document(id="1", page_content="hello", metadata={"author": "Alice"})])
        assert store.get("1") == Document(
            id="1", page_content="hello", metadata={"author": "Alice"}
        )


@persista_available
async def test_atyped_sqlite_document_store_with_metadata_schema() -> None:
    async with TypedSQLiteDocumentStore(metadata_schema={"author": "TEXT"}) as store:
        await store.aset_many(
            [Document(id="1", page_content="hello", metadata={"author": "Alice"})]
        )
        assert await store.aget("1") == Document(
            id="1", page_content="hello", metadata={"author": "Alice"}
        )
