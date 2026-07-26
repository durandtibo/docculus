r"""Helpers to detect and validate optional dependencies."""

from __future__ import annotations

__all__ = [
    "check_faker",
    "check_persista",
    "is_faker_available",
    "is_persista_available",
    "raise_faker_missing_error",
    "raise_persista_missing_error",
    "require_faker",
    "require_persista",
]

from docculus.utils.imports.faker import (
    check_faker,
    is_faker_available,
    raise_faker_missing_error,
    require_faker,
)
from docculus.utils.imports.persista import (
    check_persista,
    is_persista_available,
    raise_persista_missing_error,
    require_persista,
)
