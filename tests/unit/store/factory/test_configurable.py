from __future__ import annotations

from coola.equality import objects_are_equal

from docculus.store import InMemoryDocumentStore
from docculus.store.factory import (
    BaseDocumentStoreFactory,
    ConfigurableDocumentStoreFactory,
)
from docculus.testing.fixtures import persista_available

DOCUMENT_STORE_TARGET = "docculus.store.InMemoryDocumentStore"


def _make_document_store() -> InMemoryDocumentStore:
    """Return a document store instance for testing."""
    return InMemoryDocumentStore()


######################################################
#     Tests for ConfigurableDocumentStoreFactory     #
######################################################


# --- Inheritance ---


@persista_available
def test_configurable_document_store_factory_is_base_document_store_factory() -> None:
    assert isinstance(
        ConfigurableDocumentStoreFactory(_make_document_store()), BaseDocumentStoreFactory
    )


# --- make_document_store from instance ---


@persista_available
def test_configurable_document_store_factory_make_document_store_returns_document_store() -> None:
    factory = ConfigurableDocumentStoreFactory(_make_document_store())
    assert isinstance(factory.make_document_store(), InMemoryDocumentStore)


@persista_available
def test_configurable_document_store_factory_make_document_store_returns_same_instance() -> None:
    store = _make_document_store()
    factory = ConfigurableDocumentStoreFactory(store)
    assert factory.make_document_store() is store


# --- make_document_store from dict ---


@persista_available
def test_configurable_document_store_factory_make_document_store_from_dict_returns_document_store() -> (
    None
):
    factory = ConfigurableDocumentStoreFactory({"_target_": DOCUMENT_STORE_TARGET})
    assert isinstance(factory.make_document_store(), InMemoryDocumentStore)


# --- _get_repr_kwargs ---


@persista_available
def test_configurable_document_store_factory_get_repr_kwargs_instance() -> None:
    store = _make_document_store()
    factory = ConfigurableDocumentStoreFactory(store)
    assert objects_are_equal(factory._get_repr_kwargs(), {"document_store": store})


@persista_available
def test_configurable_document_store_factory_get_repr_kwargs_dict_input() -> None:
    config = {"_target_": DOCUMENT_STORE_TARGET}
    factory = ConfigurableDocumentStoreFactory(config)
    assert objects_are_equal(factory._get_repr_kwargs(), {"document_store": config})


# --- __repr__ and __str__ ---


@persista_available
def test_configurable_document_store_factory_repr_starts_with_class_name() -> None:
    with _make_document_store() as store:
        factory = ConfigurableDocumentStoreFactory(store)
        assert repr(factory).startswith("ConfigurableDocumentStoreFactory(")


@persista_available
def test_configurable_document_store_factory_str_starts_with_class_name() -> None:
    with _make_document_store() as store:
        factory = ConfigurableDocumentStoreFactory(store)
        assert str(factory).startswith("ConfigurableDocumentStoreFactory(")


@persista_available
def test_configurable_document_store_factory_repr_contains_document_store() -> None:
    with _make_document_store() as store:
        factory = ConfigurableDocumentStoreFactory(store)
        assert "document_store" in repr(factory)


@persista_available
def test_configurable_document_store_factory_str_contains_document_store() -> None:
    with _make_document_store() as store:
        factory = ConfigurableDocumentStoreFactory(store)
        assert "document_store" in str(factory)
