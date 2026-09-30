"""Public, read-only catalogue views.

Unlike the boilerplate ``documents`` app (login + org-scoped), the survey
catalogue is public: anyone can browse published artefacts. Editing happens in
the admin. Drafts (``is_published=False``) are hidden from the public list/detail.
"""

from django.db.models import Count, F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from catalog import rdf_sync
from catalog.models import Artefact, Findspot, ObjectCategory
from catalog.search import search_artefacts


class ArtefactListView(ListView):
    model = Artefact
    template_name = "catalog/artefact_list.html"
    context_object_name = "artefacts"
    paginate_by = 24

    # Multi-select facets. Each maps a query param to the ORM lookup it filters.
    FACETS = {
        "category": "category__in",
        "region": "region_id__in",
        "material": "materials__in",
        "script": "inscriptions__script_id__in",
        "findspot": "findspot_id__in",
    }

    def _active(self):
        """Selected values per facet (+ the ``inscribed`` boolean)."""
        params = self.request.GET
        active = {name: params.getlist(name) for name in self.FACETS}
        active["inscribed"] = params.get("inscribed") == "1"
        return active

    def _apply_facets(self, qs, active, exclude=None):
        for name, lookup in self.FACETS.items():
            if name != exclude and active.get(name):
                qs = qs.filter(**{lookup: active[name]})
        if exclude != "inscribed" and active.get("inscribed"):
            qs = qs.filter(is_inscribed=True)
        return qs.distinct()

    def _searched(self):
        """Published artefacts narrowed by the text query (no facets yet)."""
        qs = Artefact.objects.filter(is_published=True)
        return search_artefacts(qs, self.request.GET.get("q", ""))

    def get_queryset(self):
        qs = (
            self._apply_facets(self._searched(), self._active())
            .select_related("object_type", "region", "period", "findspot", "repository")
            .prefetch_related("media", "tags")
        )
        # Rank-order when a text query annotated `rank`; else newest first.
        if "q" in self.request.GET and self.request.GET.get("q", "").strip():
            try:
                return qs.order_by("-rank", "-updated_at")
            except Exception:
                pass
        return qs.order_by("-updated_at")

    def _facet_options(self, active):
        """For each facet, count matches over the results filtered by every
        *other* active facet (so selecting one value still shows siblings)."""
        searched = self._searched()

        def counts(qs, value_field, label_field=None):
            fields = [value_field] + ([label_field] if label_field else [])
            # order_by() clears the model's default ordering, which would
            # otherwise leak into GROUP BY and fragment the counts.
            rows = qs.order_by().values(*fields).annotate(n=Count("pk", distinct=True))
            return {r[value_field]: (r.get(label_field), r["n"]) for r in rows}

        options = {}

        cat = counts(self._apply_facets(searched, active, exclude="category"), "category")
        options["category"] = [
            {"value": v, "label": label, "count": cat.get(v, (None, 0))[1],
             "selected": v in active["category"]}
            for v, label in ObjectCategory.choices
            if cat.get(v, (None, 0))[1] or v in active["category"]
        ]

        reg = counts(self._apply_facets(searched, active, exclude="region"),
                     "region_id", "region__label")
        options["region"] = [
            {"value": str(pk), "label": lbl, "count": n, "selected": str(pk) in active["region"]}
            for pk, (lbl, n) in sorted(reg.items(), key=lambda x: (x[1][0] or "")) if pk
        ]

        mat = counts(self._apply_facets(searched, active, exclude="material"),
                     "materials", "materials__label")
        options["material"] = [
            {"value": str(pk), "label": lbl, "count": n, "selected": str(pk) in active["material"]}
            for pk, (lbl, n) in sorted(mat.items(), key=lambda x: (x[1][0] or "")) if pk
        ]

        scr = counts(self._apply_facets(searched, active, exclude="script"),
                     "inscriptions__script_id", "inscriptions__script__label")
        options["script"] = [
            {"value": str(pk), "label": lbl, "count": n, "selected": str(pk) in active["script"]}
            for pk, (lbl, n) in sorted(scr.items(), key=lambda x: (x[1][0] or "")) if pk
        ]
        return options

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET
        active = self._active()
        ctx["query"] = params.get("q", "")
        ctx["active"] = active
        ctx["inscribed_only"] = active["inscribed"]
        ctx["facets"] = self._facet_options(active)
        ctx["has_filters"] = bool(
            params.get("q") or active["inscribed"] or any(active[f] for f in self.FACETS)
        )
        if active["findspot"] and active["findspot"][0].isdigit():
            ctx["active_findspot"] = Findspot.objects.filter(pk=active["findspot"][0]).first()
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


class StatisticsView(TemplateView):
    """Survey statistics over published artefacts: distribution by category,
    region, period (chronological), script, material and top find spots."""

    template_name = "catalog/statistics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pub = Artefact.objects.filter(is_published=True)

        # .order_by() clears Meta.ordering so it doesn't leak into GROUP BY.
        cat_counts = dict(pub.values_list("category").order_by().annotate(n=Count("id")))
        ctx["kpis"] = kpis = {
            "total": pub.count(),
            "inscribed": pub.filter(is_inscribed=True).count(),
            "iconography": pub.filter(has_iconography=True).count(),
            "findspots": pub.exclude(findspot=None).values("findspot").distinct().count(),
            "regions": pub.exclude(region=None).values("region").distinct().count(),
        }
        ctx["kpi_tiles"] = [
            (_("Objects"), kpis["total"]),
            (_("Inscribed"), kpis["inscribed"]),
            (_("With iconography"), kpis["iconography"]),
            (_("Find spots"), kpis["findspots"]),
            (_("Regions"), kpis["regions"]),
        ]

        by_category = [
            {"label": str(label), "n": cat_counts.get(value, 0)}
            for value, label in ObjectCategory.choices
            if cat_counts.get(value, 0)
        ]
        by_region = list(
            pub.exclude(region=None).values(label=F("region__label"))
            .order_by().annotate(n=Count("id")).order_by("-n")
        )
        by_period = list(
            pub.exclude(period=None)
            .values(label=F("period__label"), start=F("period__start_year"))
            .order_by().annotate(n=Count("id")).order_by("start", "label")
        )
        by_script = list(
            pub.filter(inscriptions__script__isnull=False)
            .values(label=F("inscriptions__script__label"))
            .order_by().annotate(n=Count("id", distinct=True)).order_by("-n")
        )
        by_material = list(
            pub.filter(materials__isnull=False)
            .values(label=F("materials__label"))
            .order_by().annotate(n=Count("id", distinct=True)).order_by("-n")
        )
        top_findspots = list(
            pub.exclude(findspot=None).values(label=F("findspot__name_modern"))
            .order_by().annotate(n=Count("id")).order_by("-n")[:12]
        )

        def pack(rows):
            return {"labels": [r["label"] or "—" for r in rows], "data": [r["n"] for r in rows]}

        ctx["charts"] = {
            "category": {"labels": [r["label"] for r in by_category],
                         "data": [r["n"] for r in by_category]},
            "region": pack(by_region),
            "period": pack(by_period),
            "script": pack(by_script),
            "material": pack(by_material),
            "findspot": pack(top_findspots),
        }
        return ctx


class ArtefactRDFView(View):
    """RDF (Turtle / JSON-LD / RDF-XML / N-Triples) for one published artefact.

    Makes the artefact IRI dereferenceable for Linked Open Data clients.
    """

    def get(self, request, slug):
        artefact = get_object_or_404(Artefact.objects.filter(is_published=True), slug=slug)
        rdf_format, content_type = rdf_sync.negotiate_format(request)
        graph = rdf_sync.graph_for_artefact(artefact)
        return HttpResponse(graph.serialize(format=rdf_format), content_type=content_type)


class DatasetRDFView(View):
    """RDF dump of the whole published catalogue."""

    def get(self, request):
        rdf_format, content_type = rdf_sync.negotiate_format(request)
        graph = rdf_sync.graph_for_dataset()
        return HttpResponse(graph.serialize(format=rdf_format), content_type=content_type)
