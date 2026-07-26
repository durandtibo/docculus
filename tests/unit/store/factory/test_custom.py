from __future__ import annotations

import pytest
from coola.equality import objects_are_equal
from langchain_core.documents import Document

from docculus.store.custom import (
    DuckDBDocumentStore,
    InMemoryDocumentStore,
    SQLiteDocumentStore,
    TypedDuckDBDocumentStore,
    TypedSQLiteDocumentStore,
)
from docculus.store.factory import (
    BaseDocumentStoreFactory,
    DuckDBDocumentStoreFactory,
    InMemoryDocumentStoreFactory,
    SQLiteDocumentStoreFactory,
    TypedDuckDBDocumentStoreFactory,
    TypedSQLiteDocumentStoreFactory,
)
from docculus.testing.fixtures import persista_available
from docculus.utils.imports import is_persista_available

if is_persista_available():
    from persista.utils.imports import is_duckdb_available

pytest.importorskip("persista")

###############################################
#     Tests for InMemoryDocumentStoreFactory  #
###############################################


@persista_available
def test_in_memory_document_store_factory_is_base_document_store_factory() -> None:
    assert isinstance(InMemoryDocumentStoreFactory(), BaseDocumentStoreFactory)


@persista_available
def test_in_memory_document_store_factory_make_document_store_returns_in_memory_document_store() -> (
    None
):
    factory = InMemoryDocumentStoreFactory()
    assert isinstance(factory.make_document_store(), InMemoryDocumentStore)


@persista_available
def test_in_memory_document_store_factory_make_document_store_returns_new_instance_across_calls() -> (
    None
):
    factory = InMemoryDocumentStoreFactory()
    assert factory.make_document_store() is not factory.make_document_store()


@persista_available
def test_in_memory_document_store_factory_get_repr_kwargs() -> None:
    factory = InMemoryDocumentStoreFactory()
    assert objects_are_equal(factory._get_repr_kwargs(), {})


@persista_available
def test_in_memory_document_store_factory_repr_starts_with_class_name() -> None:
    factory = InMemoryDocumentStoreFactory()
    assert repr(factory).startswith("InMemoryDocumentStoreFactory(")


@persista_available
def test_in_memory_document_store_factory_str_starts_with_class_name() -> None:
    factory = InMemoryDocumentStoreFactory()
    assert str(factory).startswith("InMemoryDocumentStoreFactory(")


###############################################
#     Tests for SQLiteDocumentStoreFactory    #
###############################################


@persista_available
def test_sqlite_document_store_factory_is_base_document_store_factory() -> None:
    assert isinstance(SQLiteDocumentStoreFactory(), BaseDocumentStoreFactory)


@persista_available
def test_sqlite_document_store_factory_make_document_store_returns_sqlite_document_store() -> None:
    factory = SQLiteDocumentStoreFactory()
    with factory.make_document_store() as store:
        assert isinstance(store, SQLiteDocumentStore)


@persista_available
def test_sqlite_document_store_factory_make_document_store_returns_new_instance_across_calls() -> (
    None
):
    factory = SQLiteDocumentStoreFactory()
    assert factory.make_document_store() is not factory.make_document_store()


@persista_available
def test_sqlite_document_store_factory_forwards_database() -> None:
    factory = SQLiteDocumentStoreFactory(database=":memory:")
    with factory.make_document_store() as store:
        assert not store.closed


@persista_available
def test_sqlite_document_store_factory_get_repr_kwargs() -> None:
    factory = SQLiteDocumentStoreFactory(database=":memory:")
    assert objects_are_equal(factory._get_repr_kwargs(), {"database": ":memory:"})


@persista_available
def test_sqlite_document_store_factory_repr_starts_with_class_name() -> None:
    factory = SQLiteDocumentStoreFactory()
    assert repr(factory).startswith("SQLiteDocumentStoreFactory(")


@persista_available
def test_sqlite_document_store_factory_str_starts_with_class_name() -> None:
    factory = SQLiteDocumentStoreFactory()
    assert str(factory).startswith("SQLiteDocumentStoreFactory(")


#####################################################
#     Tests for TypedSQLiteDocumentStoreFactory     #
#####################################################


@persista_available
def test_typed_sqlite_document_store_factory_is_base_document_store_factory() -> None:
    assert isinstance(TypedSQLiteDocumentStoreFactory(), BaseDocumentStoreFactory)


@persista_available
def test_typed_sqlite_document_store_factory_make_document_store_returns_typed_sqlite_document_store() -> (
    None
):
    factory = TypedSQLiteDocumentStoreFactory()
    with factory.make_document_store() as store:
        assert isinstance(store, TypedSQLiteDocumentStore)


@persista_available
def test_typed_sqlite_document_store_factory_make_document_store_returns_new_instance_across_calls() -> (
    None
):
    factory = TypedSQLiteDocumentStoreFactory()
    assert factory.make_document_store() is not factory.make_document_store()


@persista_available
def test_typed_sqlite_document_store_factory_forwards_metadata_schema() -> None:
    factory = TypedSQLiteDocumentStoreFactory(metadata_schema={"author": "TEXT"})
    with factory.make_document_store() as store:
        store.set_many([Document(id="1", page_content="hello", metadata={"author": "Alice"})])
        assert store.get("1") == Document(
            id="1", page_content="hello", metadata={"author": "Alice"}
        )


@persista_available
def test_typed_sqlite_document_store_factory_get_repr_kwargs() -> None:
    factory = TypedSQLiteDocumentStoreFactory(
        database=":memory:", metadata_schema={"author": "TEXT"}
    )
    assert objects_are_equal(
        factory._get_repr_kwargs(),
        {"database": ":memory:", "metadata_schema": {"author": "TEXT"}},
    )


@persista_available
def test_typed_sqlite_document_store_factory_repr_starts_with_class_name() -> None:
    factory = TypedSQLiteDocumentStoreFactory()
    assert repr(factory).startswith("TypedSQLiteDocumentStoreFactory(")


@persista_available
def test_typed_sqlite_document_store_factory_str_starts_with_class_name() -> None:
    factory = TypedSQLiteDocumentStoreFactory()
    assert str(factory).startswith("TypedSQLiteDocumentStoreFactory(")


###############################################
#     Tests for DuckDBDocumentStoreFactory    #
###############################################


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_duckdb_document_store_factory_is_base_document_store_factory() -> None:
    assert isinstance(DuckDBDocumentStoreFactory(), BaseDocumentStoreFactory)


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_duckdb_document_store_factory_make_document_store_returns_duckdb_document_store() -> None:
    factory = DuckDBDocumentStoreFactory()
    with factory.make_document_store() as store:
        assert isinstance(store, DuckDBDocumentStore)


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_duckdb_document_store_factory_make_document_store_returns_new_instance_across_calls() -> (
    None
):
    factory = DuckDBDocumentStoreFactory()
    assert factory.make_document_store() is not factory.make_document_store()


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_duckdb_document_store_factory_get_repr_kwargs() -> None:
    factory = DuckDBDocumentStoreFactory(database=":memory:")
    assert objects_are_equal(factory._get_repr_kwargs(), {"database": ":memory:"})


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_duckdb_document_store_factory_repr_starts_with_class_name() -> None:
    factory = DuckDBDocumentStoreFactory()
    assert repr(factory).startswith("DuckDBDocumentStoreFactory(")


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_duckdb_document_store_factory_str_starts_with_class_name() -> None:
    factory = DuckDBDocumentStoreFactory()
    assert str(factory).startswith("DuckDBDocumentStoreFactory(")


#####################################################
#     Tests for TypedDuckDBDocumentStoreFactory     #
#####################################################


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_typed_duckdb_document_store_factory_is_base_document_store_factory() -> None:
    assert isinstance(TypedDuckDBDocumentStoreFactory(), BaseDocumentStoreFactory)


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_typed_duckdb_document_store_factory_make_document_store_returns_typed_duckdb_document_store() -> (
    None
):
    factory = TypedDuckDBDocumentStoreFactory()
    with factory.make_document_store() as store:
        assert isinstance(store, TypedDuckDBDocumentStore)


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_typed_duckdb_document_store_factory_make_document_store_returns_new_instance_across_calls() -> (
    None
):
    factory = TypedDuckDBDocumentStoreFactory()
    assert factory.make_document_store() is not factory.make_document_store()


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_typed_duckdb_document_store_factory_forwards_metadata_schema() -> None:
    factory = TypedDuckDBDocumentStoreFactory(metadata_schema={"author": "TEXT"})
    with factory.make_document_store() as store:
        store.set_many([Document(id="1", page_content="hello", metadata={"author": "Alice"})])
        assert store.get("1") == Document(
            id="1", page_content="hello", metadata={"author": "Alice"}
        )


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_typed_duckdb_document_store_factory_get_repr_kwargs() -> None:
    factory = TypedDuckDBDocumentStoreFactory(
        database=":memory:", metadata_schema={"author": "TEXT"}
    )
    assert objects_are_equal(
        factory._get_repr_kwargs(),
        {"database": ":memory:", "metadata_schema": {"author": "TEXT"}},
    )


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_typed_duckdb_document_store_factory_repr_starts_with_class_name() -> None:
    factory = TypedDuckDBDocumentStoreFactory()
    assert repr(factory).startswith("TypedDuckDBDocumentStoreFactory(")


@pytest.mark.skipif(not is_duckdb_available(), reason="duckdb is not installed")
@persista_available
def test_typed_duckdb_document_store_factory_str_starts_with_class_name() -> None:
    factory = TypedDuckDBDocumentStoreFactory()
    assert str(factory).startswith("TypedDuckDBDocumentStoreFactory(")
