"""Pluggable document search.

Default backend is Postgres full-text search (no extra infrastructure). Set
``SEARCH_BACKEND = "elasticsearch"`` (+ ``ELASTICSEARCH_URL``) to route search and
indexing through an Elasticsearch cluster. All Elasticsearch access is lazy and
guarded, so the default install never imports or contacts Elasticsearch.
"""

from django.conf import settings
from django.db import connection
from django.db.models import Q


def _backend():
    return getattr(settings, "SEARCH_BACKEND", "database")


def elasticsearch_enabled():
    return _backend() == "elasticsearch"


# --- Database (Postgres FTS / sqlite fallback) -----------------------------
def _database_search(queryset, query):
    if connection.vendor == "postgresql":
        from django.contrib.postgres.search import SearchQuery, SearchVector

        return queryset.annotate(search=SearchVector("title", "description")).filter(
            search=SearchQuery(query)
        )
    return queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))


# --- Elasticsearch ---------------------------------------------------------
def _es_client():
    from elasticsearch import Elasticsearch

    return Elasticsearch(settings.ELASTICSEARCH_URL)


def _es_document(document):
    return {
        "organization_id": document.organization_id,
        "title": document.title,
        "description": document.description,
        "status": document.status,
    }


def index_document(document):
    if not elasticsearch_enabled():
        return
    _es_client().index(
        index=settings.ELASTICSEARCH_INDEX, id=document.pk, document=_es_document(document)
    )


def delete_document(document):
    if not elasticsearch_enabled():
        return
    try:
        _es_client().delete(index=settings.ELASTICSEARCH_INDEX, id=document.pk)
    except Exception:
        # Deleting a document that was never indexed must not break the request.
        pass


def _es_search_ids(organization, query):
    response = _es_client().search(
        index=settings.ELASTICSEARCH_INDEX,
        query={
            "bool": {
                "must": [{"multi_match": {"query": query, "fields": ["title", "description"]}}],
                "filter": [{"term": {"organization_id": organization.id}}],
            }
        },
    )
    return [int(hit["_id"]) for hit in response["hits"]["hits"]]


# --- Public API ------------------------------------------------------------
def search_documents(queryset, query, organization):
    """Filter an (already org-scoped) Document queryset by a search query."""
    query = (query or "").strip()
    if not query:
        return queryset
    if elasticsearch_enabled():
        ids = _es_search_ids(organization, query)
        return queryset.filter(pk__in=ids)
    return _database_search(queryset, query)
