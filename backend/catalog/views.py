"""Public, read-only catalogue views.

Unlike the boilerplate ``documents`` app (login + org-scoped), the survey
catalogue is public: anyone can browse published artefacts. Editing happens in
the admin. Drafts (``is_published=False``) are hidden from the public list/detail.
"""

from django.db.models import Count, Q
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView

from catalog.models import Artefact, Findspot, ObjectCategory, Region


class ArtefactListView(ListView):
    model = Artefact
    template_name = "catalog/artefact_list.html"
    context_object_name = "artefacts"
    paginate_by = 24

    def get_queryset(self):
        qs = (
            Artefact.objects.filter(is_published=True)
            .select_related("object_type", "region", "period", "findspot", "repository")
            .prefetch_related("media", "tags")
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(notes__icontains=query)
                | Q(ruler__icontains=query)
                | Q(identifiers__value__icontains=query)
            ).distinct()
        category = self.request.GET.get("category", "")
        if category:
            qs = qs.filter(category=category)
        region = self.request.GET.get("region", "")
        if region.isdigit():
            qs = qs.filter(region_id=int(region))
        findspot = self.request.GET.get("findspot", "")
        if findspot.isdigit():
            qs = qs.filter(findspot_id=int(findspot))
        if self.request.GET.get("inscribed") == "1":
            qs = qs.filter(is_inscribed=True)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET
        ctx["query"] = params.get("q", "")
        ctx["selected_category"] = params.get("category", "")
        ctx["selected_region"] = params.get("region", "")
        ctx["inscribed_only"] = params.get("inscribed") == "1"
        ctx["categories"] = ObjectCategory.choices
        ctx["regions"] = Region.objects.all()
        findspot = params.get("findspot", "")
        if findspot.isdigit():
            ctx["active_findspot"] = Findspot.objects.filter(pk=int(findspot)).first()
        # Preserve active filters across pagination links.
        carry = params.copy()
        carry.pop("page", None)
        ctx["querystring"] = carry.urlencode()
        return ctx


class ArtefactDetailView(DetailView):
    model = Artefact
    template_name = "catalog/artefact_detail.html"
    context_object_name = "artefact"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Artefact.objects.filter(is_published=True)
            .select_related(
                "object_type", "region", "period", "period__scheme", "findspot",
                "find_context", "find_context__excavation", "repository", "origin_region",
            )
            .prefetch_related(
                "media",
                "identifiers",
                "measurements",
                "material_analyses",
                "materials",
                "iconographic_features",
                "provenance_events__repository",
                "publication_refs__publication",
                "inscriptions__script",
                "inscriptions__language",
                "inscriptions__readings",
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        media = list(self.object.media.all())
        ctx["iiif_manifests"] = [m.iiif_manifest_url for m in media if m.iiif_manifest_url]
        ctx["image_media"] = [
            m for m in media if (m.file or m.image_url) and not m.iiif_manifest_url
        ]
        return ctx


class ArtefactMapView(TemplateView):
    """Find-spot map: one marker per find spot with coordinates, sized by the
    number of published artefacts found there."""

    template_name = "catalog/artefact_map.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        findspots = (
            Findspot.objects.filter(latitude__isnull=False, longitude__isnull=False)
            .annotate(n=Count("artefacts", filter=Q(artefacts__is_published=True)))
            .filter(n__gt=0)
        )
        ctx["findspots"] = [
            {
                "name": f.name_modern,
                "ancient": f.name_ancient,
                "region": f.region.label if f.region else "",
                "lat": float(f.latitude),
                "lng": float(f.longitude),
                "count": f.n,
                "url": reverse("catalog:artefact-list") + f"?findspot={f.pk}",
            }
            for f in findspots
        ]
        return ctx
