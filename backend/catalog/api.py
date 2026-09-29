"""Public, read-only REST API for the catalogue.

Anonymous read access (Open Access / Linked Open Data goal); editing stays in
the admin. Filtering mirrors the web facets and reuses ``search_artefacts`` so
the API and the site behave identically.
"""

from django.db.models import Count, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from catalog.models import (
    Artefact,
    Findspot,
    Material,
    ObjectType,
    Period,
    Region,
    ScriptType,
)
from catalog.search import search_artefacts
from catalog.serializers import (
    ArtefactDetailSerializer,
    ArtefactListSerializer,
    FindspotSerializer,
    MaterialSerializer,
    ObjectTypeSerializer,
    PeriodSerializer,
    RegionSerializer,
    ScriptTypeSerializer,
)


class PublicReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """Base: unauthenticated read-only access."""

    permission_classes = [AllowAny]


# Multi-value filters shared by the artefact list. Maps query param -> ORM lookup.
_ARTEFACT_FILTERS = {
    "category": "category__in",
    "region": "region_id__in",
    "material": "materials__in",
    "script": "inscriptions__script_id__in",
    "findspot": "findspot_id__in",
}


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter("q", OpenApiTypes.STR, description="Full-text search query."),
            OpenApiParameter("category", OpenApiTypes.STR, many=True,
                             description="Filter by category (repeatable)."),
            OpenApiParameter("region", OpenApiTypes.INT, many=True,
                             description="Filter by region id (repeatable)."),
            OpenApiParameter("material", OpenApiTypes.INT, many=True,
                             description="Filter by material id (repeatable)."),
            OpenApiParameter("script", OpenApiTypes.INT, many=True,
                             description="Filter by script id (repeatable)."),
            OpenApiParameter("findspot", OpenApiTypes.INT, many=True,
                             description="Filter by find-spot id (repeatable)."),
            OpenApiParameter("inscribed", OpenApiTypes.BOOL,
                             description="Only inscribed objects when true."),
        ]
    )
)
class ArtefactViewSet(PublicReadOnlyViewSet):
    """Published artefacts. `retrieve` is by slug."""

    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ArtefactDetailSerializer
        return ArtefactListSerializer

    def get_queryset(self):
        qs = Artefact.objects.filter(is_published=True)
        params = self.request.query_params

        qs = search_artefacts(qs, params.get("q", ""))
        for param, lookup in _ARTEFACT_FILTERS.items():
            values = [v for v in params.getlist(param) if v]
            if values:
                qs = qs.filter(**{lookup: values})
        if params.get("inscribed") in ("1", "true", "True"):
            qs = qs.filter(is_inscribed=True)
        qs = qs.distinct()

        if self.action == "retrieve":
            return qs.select_related(
                "object_type", "region", "period", "period__scheme", "findspot",
                "findspot__region", "repository", "origin_region",
            ).prefetch_related(
                "identifiers", "measurements", "materials", "iconographic_features",
                "media", "provenance_events__repository", "publication_refs__publication",
                "inscriptions__script", "inscriptions__language", "inscriptions__readings",
            )
        qs = qs.select_related("object_type", "region", "period").prefetch_related("media")
        if params.get("q", "").strip():
            return qs.order_by("-rank", "-updated_at")
        return qs.order_by("-updated_at")


class FindspotViewSet(PublicReadOnlyViewSet):
    """Find spots that have at least one published artefact (for maps)."""

    serializer_class = FindspotSerializer

    def get_queryset(self):
        return (
            Findspot.objects.annotate(
                artefact_count=Count("artefacts", filter=Q(artefacts__is_published=True))
            )
            .filter(artefact_count__gt=0)
            .select_related("region")
        )


class RegionViewSet(PublicReadOnlyViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class PeriodViewSet(PublicReadOnlyViewSet):
    queryset = Period.objects.select_related("scheme").all()
    serializer_class = PeriodSerializer


class ObjectTypeViewSet(PublicReadOnlyViewSet):
    queryset = ObjectType.objects.all()
    serializer_class = ObjectTypeSerializer


class MaterialViewSet(PublicReadOnlyViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer


class ScriptTypeViewSet(PublicReadOnlyViewSet):
    queryset = ScriptType.objects.all()
    serializer_class = ScriptTypeSerializer
