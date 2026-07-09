"""Full-text search for the catalogue.

Postgres full-text search with ranking over the artefact's core text fields,
plus substring matching for short codes and epigraphic strings (inventory
numbers, transliterations) where FTS stemming would hurt. Falls back to
``icontains`` on SQLite so tests and quick local runs still work.

Kept on-the-fly (no stored SearchVectorField) to mirror the boilerplate's
``documents`` app. For a large corpus, promote to a stored ``SearchVectorField``
+ ``GinIndex`` maintained by signals — see docs/catalog-data-model.md.
"""

from django.db import connection
from django.db.models import Q


def _substring_q(query):
    """Match short/epigraphic fields where stemmed FTS is inappropriate."""
    return (
        Q(identifiers__value__icontains=query)
        | Q(inscriptions__readings__reading_normalized__icontains=query)
        | Q(inscriptions__readings__transliteration__icontains=query)
        | Q(inscriptions__readings__translation_en__icontains=query)
    )


def search_artefacts(queryset, query):
    """Filter and rank an Artefact queryset by a free-text query.

    Returns the queryset unchanged when the query is empty. When ranked, the
    queryset carries a ``rank`` annotation so callers can order by ``-rank``.
    """
    query = (query or "").strip()
    if not query:
        return queryset

    if connection.vendor == "postgresql":
        from django.contrib.postgres.search import (
            SearchQuery,
            SearchRank,
            SearchVector,
        )

        vector = (
            SearchVector("title", weight="A", config="english")
            + SearchVector("ruler", weight="B", config="english")
            + SearchVector("description", weight="C", config="english")
            + SearchVector("notes", weight="D", config="english")
        )
        search_query = SearchQuery(query, search_type="websearch", config="english")
        # Filter by tsvector MATCH (@@) — respects websearch operators such as
        # negation and phrases. SearchRank is only for ordering (ts_rank does not
        # honour negation as a boolean, so it must not be used to filter).
        return (
            queryset.annotate(
                search=vector, rank=SearchRank(vector, search_query)
            )
            .filter(Q(search=search_query) | _substring_q(query))
            .distinct()
        )

    # SQLite / other: plain substring fallback.
    return queryset.filter(
        Q(title__icontains=query)
        | Q(description__icontains=query)
        | Q(notes__icontains=query)
        | Q(ruler__icontains=query)
        | _substring_q(query)
    ).distinct()
