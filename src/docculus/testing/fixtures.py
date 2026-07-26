r"""Define some pytest fixtures for testing.

`pytest` is required to use these fixtures.
"""

from __future__ import annotations

__all__ = ["persista_available", "persista_not_available"]

import pytest

from docculus.utils.imports import is_persista_available

persista_available: pytest.MarkDecorator = pytest.mark.skipif(
    not is_persista_available(), reason="Requires persista"
)
persista_not_available: pytest.MarkDecorator = pytest.mark.skipif(
    is_persista_available(), reason="Skip if persista is available"
)
