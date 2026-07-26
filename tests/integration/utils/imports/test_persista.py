from __future__ import annotations

import pytest

from docculus.testing.fixtures import persista_available, persista_not_available
from docculus.utils.imports import check_persista, is_persista_available

####################
#     persista     #
####################


@persista_available
def test_check_persista_with_package() -> None:
    check_persista()


@persista_not_available
def test_check_persista_without_package() -> None:
    with pytest.raises(RuntimeError, match=r"'persista' package is required but not installed."):
        check_persista()


@persista_available
def test_is_persista_available_true() -> None:
    assert is_persista_available()


@persista_not_available
def test_is_persista_available_false() -> None:
    assert not is_persista_available()
