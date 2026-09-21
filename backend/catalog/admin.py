from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline

from catalog.bibtex import apply_entry, import_bibtex, parse_bibtex

from catalog.models import (
    Artefact,
    Excavation,
    Findspot,
    IconographicMotif,
    Identifier,
    Inscription,
    Language,
    Material,
    MaterialAnalysis,
    Measurement,
    MediaItem,
    ObjectType,
    Period,
    PeriodScheme,
    ProvenanceEvent,
    Publication,
    PublicationReference,
    Reading,
    Region,
    Repository,
    ScriptType,
    StratigraphicContext,
)


# ---- Inlines on the artefact form -----------------------------------------
class IdentifierInline(TabularInline):
    model = Identifier
    extra = 1


class MeasurementInline(TabularInline):
    model = Measurement
    extra = 0
    autocomplete_fields = ("source",)


class MediaItemInline(TabularInline):
    model = MediaItem
    extra = 0


class InscriptionInline(TabularInline):
    model = Inscription
    extra = 0
    autocomplete_fields = ("script", "language")
    fields = ("script", "language", "technique", "position", "line_count")
    show_change_link = True


class ProvenanceEventInline(TabularInline):
    model = ProvenanceEvent
    extra = 0
    autocomplete_fields = ("repository",)


class PublicationReferenceInline(TabularInline):
    model = PublicationReference
    extra = 0
    autocomplete_fields = ("publication",)


class MaterialAnalysisInline(TabularInline):
    model = MaterialAnalysis
    extra = 0
    autocomplete_fields = ("source",)


@admin.register(Artefact)
class ArtefactAdmin(ModelAdmin, SimpleHistoryAdmin):
    list_display = (
        "title", "category", "object_type", "region", "period",
        "is_inscribed", "has_iconography", "is_published", "repository", "updated_at",
    )
    list_filter = (
        "category", "is_published", "is_inscribed", "has_iconography", "condition",
        "region", "period", "object_type",
    )
    search_fields = ("title", "description", "notes", "identifiers__value", "ruler")
    autocomplete_fields = (
        "organization", "object_type", "findspot", "find_context", "region",
        "repository", "period", "origin_region",
    )
    filter_horizontal = ("materials", "iconographic_features")
    readonly_fields = ("uuid", "slug", "created_at", "updated_at")
    inlines = [
        IdentifierInline, MediaItemInline, InscriptionInline, MeasurementInline,
        MaterialAnalysisInline, ProvenanceEventInline, PublicationReferenceInline,
    ]
    fieldsets = (
        (None, {"fields": ("title", "category", "object_type", "tags")}),
        ("Find context", {"fields": ("findspot", "find_context", "region")}),
        ("Dating & attribution", {"fields": ("period", "dating_text", "ruler")}),
        ("Origin", {"fields": ("origin_region", "origin_note")}),
        ("Keeping & condition", {"fields": ("repository", "condition", "preservation_note")}),
        ("Content", {"fields": (
            "is_inscribed", "has_iconography", "is_published",
            "materials", "iconographic_features",
        )}),
        ("Description", {"fields": ("description", "notes")}),
        ("System", {
            "fields": ("uuid", "slug", "organization", "created_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class ReadingInline(TabularInline):
    model = Reading
    extra = 1
    fields = (
        "reading_normalized", "transliteration", "translation_en",
        "certainty", "is_preferred", "generated_by_model",
    )


@admin.register(Inscription)
class InscriptionAdmin(ModelAdmin, SimpleHistoryAdmin):
    list_display = ("artefact", "script", "language", "technique", "line_count")
    list_filter = ("script", "language")
    search_fields = ("artefact__title", "notes")
    autocomplete_fields = ("organization", "artefact", "script", "language")
    inlines = [ReadingInline]


@admin.register(Reading)
class ReadingAdmin(ModelAdmin, SimpleHistoryAdmin):
    list_display = ("__str__", "inscription", "certainty", "is_preferred", "generated_by_model")
    list_filter = ("certainty", "is_preferred", "generated_by_model")
    search_fields = ("reading_normalized", "transliteration", "translation_en")
    autocomplete_fields = ("inscription",)
    filter_horizontal = ("publications",)


# ---- Controlled vocabularies ----------------------------------------------
@admin.register(ObjectType, Material, ScriptType, Language)
class ControlledTermAdmin(ModelAdmin):
    list_display = ("label", "skos_uri")
    search_fields = ("label", "description")


@admin.register(IconographicMotif)
class IconographicMotifAdmin(ModelAdmin):
    list_display = ("label", "broader", "skos_uri")
    list_filter = ("broader",)
    search_fields = ("label", "description")
    autocomplete_fields = ("broader",)


@admin.register(Region)
class RegionAdmin(ModelAdmin):
    list_display = ("label", "parent", "skos_uri")
    list_filter = ("parent",)
    search_fields = ("label", "description")
    autocomplete_fields = ("parent",)


@admin.register(PeriodScheme)
class PeriodSchemeAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Period)
class PeriodAdmin(ModelAdmin):
    list_display = ("label", "scheme", "start_year", "end_year")
    list_filter = ("scheme",)
    search_fields = ("label",)
    autocomplete_fields = ("scheme",)


# ---- Places, excavations, repositories, bibliography ----------------------
@admin.register(Repository)
class RepositoryAdmin(ModelAdmin):
    list_display = ("name", "city", "country")
    search_fields = ("name", "city", "country")


@admin.register(Findspot)
class FindspotAdmin(ModelAdmin):
    list_display = ("name_modern", "name_ancient", "region", "country")
    list_filter = ("region", "country")
    search_fields = ("name_modern", "name_ancient")
    autocomplete_fields = ("region",)


@admin.register(Excavation)
class ExcavationAdmin(ModelAdmin):
    list_display = ("title", "director", "years", "findspot")
    search_fields = ("title", "director")
    autocomplete_fields = ("findspot",)


@admin.register(StratigraphicContext)
class StratigraphicContextAdmin(ModelAdmin):
    list_display = ("__str__", "excavation", "stratum", "period")
    list_filter = ("excavation", "period")
    search_fields = ("locus", "stratum", "area")
    autocomplete_fields = ("excavation", "period")


@admin.register(Publication)
class PublicationAdmin(ModelAdmin):
    list_display = ("bibtex_key", "authors", "year", "title")
    search_fields = ("bibtex_key", "authors", "title", "bibtex_raw")
    change_list_template = "admin/catalog/publication_change_list.html"

    def save_model(self, request, obj, form, change):
        """If BibTeX was pasted into bibtex_raw, parse it to fill the fields."""
        if obj.bibtex_raw and obj.bibtex_raw.strip():
            entries = parse_bibtex(obj.bibtex_raw)
            if entries:
                apply_entry(entries[0], obj)
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "import-bibtex/",
                self.admin_site.admin_view(self.import_bibtex_view),
                name="catalog_publication_import_bibtex",
            )
        ]
        return custom + urls

    def import_bibtex_view(self, request):
        if request.method == "POST":
            text = request.POST.get("bibtex", "")
            created, updated, errors = import_bibtex(text)
            if created or updated:
                messages.success(
                    request, f"Imported {created} new and updated {updated} publication(s)."
                )
            if not created and not updated and not errors:
                messages.warning(request, "No valid BibTeX entries found.")
            for err in errors:
                messages.error(request, f"Skipped {err}")
            return redirect("admin:catalog_publication_changelist")
        context = {
            **self.admin_site.each_context(request),
            "title": "Import BibTeX",
            "opts": self.model._meta,
        }
        return render(request, "admin/catalog/import_bibtex.html", context)
