r"""Contain factories for document stores."""

from __future__ import annotations

__all__ = [
    "BaseDocumentStoreFactory",
    "ConfigurableDocumentStoreFactory",
    "DocumentStoreFactory",
    "StoreDocumentStoreFactory",
]

from docculus.store.factory.base import BaseDocumentStoreFactory
from docculus.store.factory.configurable import ConfigurableDocumentStoreFactory
from docculus.store.factory.store import StoreDocumentStoreFactory
from docculus.store.factory.vanilla import DocumentStoreFactory
