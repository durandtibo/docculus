from __future__ import annotations

import pytest
from coola.equality import objects_are_equal
from langchain_core.documents import Document

from docculus.store import DocumentStore
from docculus.store.factory import BaseDocumentStoreFactory, StoreDocumentStoreFactory
from docculus.testing.fixtures import persista_available
from docculus.utils.imports import is_persista_available

if is_persista_available():
    from persista.store import InMemoryStore
    from persista.store.factory import StoreFactory

pytest.importorskip("persista")

###############################################
#     Tests for StoreDocumentStoreFactory     #
###############################################


# --- Inheritance ---


@persista_available
def test_store_document_store_factory_is_base_document_store_factory() -> None:
    assert isinstance(
        StoreDocumentStoreFactory(StoreFactory(InMemoryStore())), BaseDocumentStoreFactory
    )


# --- make_document_store ---


@persista_available
def test_store_document_store_factory_make_document_store_returns_document_store() -> None:
    factory = StoreDocumentStoreFactory(StoreFactory(InMemoryStore()))
    assert isinstance(factory.make_document_store(), DocumentStore)


@persista_available
def test_store_document_store_factory_make_document_store_uses_store_from_store_factory() -> None:
    store = InMemoryStore()
    factory = StoreDocumentStoreFactory(StoreFactory(store))
    document_store = factory.make_document_store()
    document_store.open()
    document_store.set_many([Document(id="1", page_content="hello")])
    assert store.get("1")["page_content"] == "hello"


@persista_available
def test_store_document_store_factory_make_document_store_returns_new_instance_across_calls() -> (
    None
):
    factory = StoreDocumentStoreFactory(StoreFactory(InMemoryStore()))
    assert factory.make_document_store() is not factory.make_document_store()


@persista_available
def test_store_document_store_factory_make_document_store_forwards_metadata_mode() -> None:
    factory = StoreDocumentStoreFactory(StoreFactory(InMemoryStore()), metadata_mode="single")
    assert factory.make_document_store().metadata_mode == "single"


# --- _get_repr_kwargs ---


@persista_available
def test_store_document_store_factory_get_repr_kwargs() -> None:
    store_factory = StoreFactory(InMemoryStore())
    factory = StoreDocumentStoreFactory(store_factory, metadata_mode="single")
    assert objects_are_equal(
        factory._get_repr_kwargs(),
        {"store_factory": store_factory, "metadata_mode": "single"},
    )


# --- __repr__ and __str__ ---


@persista_available
def test_store_document_store_factory_repr_starts_with_class_name() -> None:
    with InMemoryStore() as store:
        factory = StoreDocumentStoreFactory(StoreFactory(store))
        assert repr(factory).startswith("StoreDocumentStoreFactory(")


@persista_available
def test_store_document_store_factory_str_starts_with_class_name() -> None:
    with InMemoryStore() as store:
        factory = StoreDocumentStoreFactory(StoreFactory(store))
        assert str(factory).startswith("StoreDocumentStoreFactory(")


@persista_available
def test_store_document_store_factory_repr_contains_store_factory() -> None:
    with InMemoryStore() as store:
        factory = StoreDocumentStoreFactory(StoreFactory(store))
        assert "store_factory" in repr(factory)


@persista_available
def test_store_document_store_factory_str_contains_store_factory() -> None:
    with InMemoryStore() as store:
        factory = StoreDocumentStoreFactory(StoreFactory(store))
        assert "store_factory" in str(factory)
