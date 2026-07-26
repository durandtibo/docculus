r"""Helpers to detect and validate optional dependencies."""

from __future__ import annotations

__all__ = [
    "check_persista",
    "is_persista_available",
    "persista_available",
    "raise_persista_missing_error",
]


from docculus.utils.imports.persista import (
    check_persista,
    is_persista_available,
    persista_available,
    raise_persista_missing_error,
)
