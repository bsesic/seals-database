"""Full-text search for the catalogue.

Default backend is Postgres full-text search (ranked, no extra infrastructure).
Set ``SEARCH_BACKEND = "elasticsearch"`` (+ ``ELASTICSEARCH_URL``) to route search
and indexing through Elasticsearch. All Elasticsearch access is lazy and guarded,
so the default install never imports or contacts Elasticsearch.

Both backends return a queryset carrying a ``rank`` annotation so callers can
``order_by("-rank")`` — for Elasticsearch the rank preserves the relevance order
of the hits.
"""

from django.conf import settings
from django.db import connection
from django.db.models import Case, IntegerField, Q, Value, When


def _substring_q(query):
    """Match short/epigraphic fields where stemmed FTS is inappropriate."""
    return (
        Q(identifiers__value__icontains=query)
        | Q(inscriptions__readings__reading_normalized__icontains=query)
        | Q(inscriptions__readings__transliteration__icontains=query)
        | Q(inscriptions__readings__translation_en__icontains=query)
    )


# --- Backend selection -----------------------------------------------------
def _backend():
    return getattr(settings, "SEARCH_BACKEND", "database")


def elasticsearch_enabled():
    return _backend() == "elasticsearch"


def _index_name():
    return getattr(settings, "ELASTICSEARCH_CATALOG_INDEX", "catalog-artefacts")


def _es_client():
    from elasticsearch import Elasticsearch

    return Elasticsearch(settings.ELASTICSEARCH_URL)


# --- Elasticsearch indexing ------------------------------------------------
def artefact_document(artefact):
    """The Elasticsearch document for an artefact.

    Inscription readings and identifiers are flattened into ``content`` so they
    are searchable alongside the core text fields.
    """
    content = []
    for identifier in artefact.identifiers.all():
        content.append(identifier.value)
    for inscription in artefact.inscriptions.all():
        for reading in inscription.readings.all():
            content += [
                reading.reading_normalized,
                reading.transliteration,
                reading.translation_en,
            ]
    return {
        "title": artefact.title,
        "ruler": artefact.ruler,
        "description": artefact.description,
        "notes": artefact.notes,
        "category": artefact.category,
        "is_published": artefact.is_published,
        "content": " ".join(c for c in content if c),
    }


def index_artefact(artefact):
    if not elasticsearch_enabled():
        return
    _es_client().index(
        index=_index_name(), id=artefact.pk, document=artefact_document(artefact)
    )


def delete_artefact(artefact):
    if not elasticsearch_enabled():
        return
    try:
        _es_client().delete(index=_index_name(), id=artefact.pk)
    except Exception:
        # Deleting a document that was never indexed must not break the request.
        pass


def reindex_all():
    """(Re)index every published artefact. Returns the number indexed."""
    if not elasticsearch_enabled():
        return 0
    from catalog.models import Artefact

    client = _es_client()
    count = 0
    queryset = (
        Artefact.objects.filter(is_published=True)
        .prefetch_related("identifiers", "inscriptions__readings")
    )
    for artefact in queryset:
        client.index(index=_index_name(), id=artefact.pk, document=artefact_document(artefact))
        count += 1
    return count


def _es_search_ids(query):
    response = _es_client().search(
        index=_index_name(),
        query={
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "ruler^2", "description", "notes", "content"],
                        }
                    }
                ],
                "filter": [{"term": {"is_published": True}}],
            }
        },
    )
    return [int(hit["_id"]) for hit in response["hits"]["hits"]]


def _rank_by_ids(queryset, ids):
    """Filter to the given pks and annotate ``rank`` preserving their order."""
    if not ids:
        return queryset.none()
    whens = [When(pk=pk, then=Value(len(ids) - i)) for i, pk in enumerate(ids)]
    return queryset.filter(pk__in=ids).annotate(
        rank=Case(*whens, default=Value(0), output_field=IntegerField())
    )


# --- Postgres full-text search (default) -----------------------------------
def _database_search(queryset, query):
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


def search_artefacts(queryset, query):
    """Filter and rank an Artefact queryset by a free-text query.

    Returns the queryset unchanged when the query is empty. When it matches, the
    result carries a ``rank`` annotation so callers can ``order_by("-rank")``.
    """
    query = (query or "").strip()
    if not query:
        return queryset
    if elasticsearch_enabled():
        return _rank_by_ids(queryset, _es_search_ids(query))
    return _database_search(queryset, query)
