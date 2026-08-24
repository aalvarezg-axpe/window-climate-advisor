"""Shared pytest fixtures."""

from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> Iterator[None]:
    """Allow tests to load the local custom integration."""
    yield
