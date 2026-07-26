from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from docculus.utils.imports import (
    check_persista,
    is_persista_available,
    raise_persista_missing_error,
    require_persista,
)

logger = logging.getLogger(__name__)


MODULE = "docculus.utils.imports.persista"


@pytest.fixture(autouse=True)
def _cache_clear() -> None:
    is_persista_available.cache_clear()


def my_function(n: int = 0) -> int:
    return 42 + n


####################
#     persista     #
####################


def test_check_persista_with_package() -> None:
    with patch(f"{MODULE}.is_persista_available", lambda: True):
        check_persista()


def test_check_persista_without_package() -> None:
    with (
        patch(f"{MODULE}.is_persista_available", lambda: False),
        pytest.raises(RuntimeError, match=r"'persista' package is required but not installed."),
    ):
        check_persista()


def test_is_persista_available() -> None:
    assert isinstance(is_persista_available(), bool)


def test_require_persista_with_package() -> None:
    with patch(f"{MODULE}.is_persista_available", lambda: True):
        fn = require_persista(my_function)
        assert fn(2) == 44


def test_require_persista_without_package() -> None:
    with patch(f"{MODULE}.is_persista_available", lambda: False):
        fn = require_persista(my_function)
        assert fn(2) is None


def test_require_persista_decorator_with_package() -> None:
    with patch(f"{MODULE}.is_persista_available", lambda: True):

        @require_persista
        def fn(n: int = 0) -> int:
            return 42 + n

        assert fn(2) == 44


def test_require_persista_decorator_without_package() -> None:
    with patch(f"{MODULE}.is_persista_available", lambda: False):

        @require_persista
        def fn(n: int = 0) -> int:
            return 42 + n

        assert fn(2) is None


def test_raise_persista_missing_error() -> None:
    with pytest.raises(RuntimeError, match=r"'persista' package is required but not installed."):
        raise_persista_missing_error()
