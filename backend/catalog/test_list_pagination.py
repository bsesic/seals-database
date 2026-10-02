"""Page-size selector on the public catalogue list."""

from django.test import RequestFactory

from catalog.views import ArtefactListView


def _paginate_by(query):
    view = ArtefactListView()
    view.request = RequestFactory().get("/catalog/", query)
    return view.get_paginate_by(None)


def test_default_page_size_without_param():
    assert _paginate_by({}) == ArtefactListView.paginate_by


def test_allowed_page_size_is_honoured():
    for choice in ArtefactListView.PER_PAGE_CHOICES:
        assert _paginate_by({"per_page": str(choice)}) == choice


def test_disallowed_page_size_falls_back_to_default():
    # Value outside the allow-list must not let a client request huge pages.
    assert _paginate_by({"per_page": "1000"}) == ArtefactListView.paginate_by


def test_non_numeric_page_size_falls_back_to_default():
    assert _paginate_by({"per_page": "lots"}) == ArtefactListView.paginate_by
