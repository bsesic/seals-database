"""Shared pytest fixtures for the boilerplate test suite."""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()


@pytest.fixture(autouse=True)
def _clear_cache():
    """Reset the cache between tests so rate-limit counters don't leak."""
    cache.clear()
    yield


@pytest.fixture
def make_user(db):
    """Factory fixture that creates users with unique usernames/emails."""
    counter = {"n": 0}

    def _make(username=None, password="testpass123", **extra):
        counter["n"] += 1
        n = counter["n"]
        return User.objects.create_user(
            username=username or f"user{n}",
            email=extra.pop("email", f"user{n}@example.com"),
            password=password,
            **extra,
        )

    return _make
