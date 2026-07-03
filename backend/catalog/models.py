"""Data model for the Southern Levantine Stamp Seals & Bullae corpus.

Survey-MVP, relational-first. Designed so that an RDF / SPARQL (Apache Jena
Fuseki) layer and a CIDOC-CRM / SKOS mapping can be added later without
reshaping the tables — see ``docs/`` (knowledge-graph notes).

Two tiers:

* **Controlled vocabularies & shared reference data** (object types, materials,
  scripts, languages, iconographic motifs, regions, periods, repositories,
  find spots, excavations, publications). Global lookup tables, reused across
  artefacts; each carries an optional ``skos_uri`` / external URI so it can be
  aligned with the CSSL corpus and other Linked Open Data later.
* **Tenant-owned records** (the artefact and everything hanging off it).
  These inherit ``OrganizationOwnedModel`` exactly like the boilerplate's
  ``documents`` app, so the future multi-user "scholar's desk" works out of the
  box. For the solo survey everything lives in your personal organization.
"""

import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from taggit.managers import TaggableManager

from organizations.models import OrganizationOwnedModel


# ---------------------------------------------------------------------------
# Abstract bases
# ---------------------------------------------------------------------------
class TimeStampedModel(models.Model):
    """Audit columns: who created it and when it changed."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ControlledTerm(TimeStampedModel):
    """SKOS-style controlled-vocabulary term (global reference data)."""

    label = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    skos_uri = models.URLField(
        blank=True, help_text=_("External SKOS / LOD concept URI (e.g. CSSL, AAT).")
    )

    class Meta:
        abstract = True
        ordering = ["label"]

    def __str__(self):
        return self.label


# ---------------------------------------------------------------------------
# Controlled vocabularies
# ---------------------------------------------------------------------------
class ObjectType(ControlledTerm):
    """Fine-grained typology, e.g. 'Scaraboid', 'Conoid stamp seal', 'Jehud stamp impression'."""


class Material(ControlledTerm):
    """e.g. 'Limestone', 'Steatite', 'Carnelian', 'Clay (bulla)'."""


class ScriptType(ControlledTerm):
    """e.g. 'Palaeo-Hebrew', 'Neo-Palaeo-Hebrew', 'Imperial Aramaic', 'Phoenician'."""


class Language(ControlledTerm):
    """e.g. 'Hebrew', 'Aramaic', 'Ammonite', 'Moabite', 'Edomite'."""


class IconographicMotif(ControlledTerm):
    """An iconographic feature/motif (winged scarab, lion, rosette, ankh, …).

    ``broader`` enables a simple SKOS broader/narrower hierarchy so motifs can be
    grouped (e.g. 'four-winged scarab' broader 'scarab').
    """

    broader = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="narrower",
    )


class Region(ControlledTerm):
    """Historical / geographical region. Hierarchical via ``parent``.

    e.g. 'Judah', 'Samaria', 'Transjordan' › 'Ammon' / 'Moab' / 'Edom'.
    """

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )


class PeriodScheme(TimeStampedModel):
    """A chronological scheme. Different excavations date periods differently,
    so periods always belong to a named scheme."""

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Period(TimeStampedModel):
    """A named period within a scheme. Years are integers, BCE negative
    (e.g. Iron IIC ≈ -700 … -586; Persian ≈ -539 … -332)."""

    scheme = models.ForeignKey(
        PeriodScheme, on_delete=models.CASCADE, related_name="periods"
    )
    label = models.CharField(max_length=200)
    start_year = models.IntegerField(
        null=True, blank=True, help_text=_("BCE as negative integer.")
    )
    end_year = models.IntegerField(null=True, blank=True)
    skos_uri = models.URLField(blank=True, help_text=_("e.g. a PeriodO / Chronontology URI."))

    class Meta:
        ordering = ["scheme", "start_year", "label"]
        unique_together = [("scheme", "label")]

    def __str__(self):
        return f"{self.label} ({self.scheme})"


# ---------------------------------------------------------------------------
# Places, excavations, repositories, bibliography (shared reference data)
# ---------------------------------------------------------------------------
class Repository(TimeStampedModel):
    """Where an object is (or was) kept: museum, IAA storage, private collection."""

    name = models.CharField(max_length=255)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "repositories"

    def __str__(self):
        return self.name


class Findspot(TimeStampedModel):
    """A find location (modern site)."""

    name_modern = models.CharField(max_length=255)
    name_ancient = models.CharField(max_length=255, blank=True)
    region = models.ForeignKey(
        Region, null=True, blank=True, on_delete=models.SET_NULL, related_name="findspots"
    )
    country = models.CharField(max_length=120, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    gazetteer_uri = models.URLField(
        blank=True, help_text=_("Pleiades / iDAI.gazetteer / GeoNames URI.")
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name_modern"]

    def __str__(self):
        return self.name_modern


class Excavation(TimeStampedModel):
    """An excavation / survey project at a find spot."""

    title = models.CharField(max_length=255)
    director = models.CharField(max_length=255, blank=True)
    years = models.CharField(max_length=120, blank=True, help_text=_("e.g. '1932–1938'."))
    findspot = models.ForeignKey(
        Findspot, null=True, blank=True, on_delete=models.SET_NULL, related_name="excavations"
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class StratigraphicContext(TimeStampedModel):
    """Find context within an excavation: area / locus / stratum, with a dating period."""

    excavation = models.ForeignKey(
        Excavation, on_delete=models.CASCADE, related_name="contexts"
    )
    area = models.CharField(max_length=120, blank=True)
    locus = models.CharField(max_length=120, blank=True)
    stratum = models.CharField(max_length=120, blank=True)
    period = models.ForeignKey(
        Period, null=True, blank=True, on_delete=models.SET_NULL, related_name="contexts"
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["excavation", "stratum", "locus"]

    def __str__(self):
        bits = [self.excavation.title]
        if self.area:
            bits.append(f"Area {self.area}")
        if self.locus:
            bits.append(f"Locus {self.locus}")
        if self.stratum:
            bits.append(f"Stratum {self.stratum}")
        return " · ".join(bits)


class Publication(TimeStampedModel):
    """Bibliographic record, BibTeX-first.

    Keep the raw BibTeX as the source of truth; the parsed/cached fields are for
    display, search and a cached DIN-style citation.
    """

    bibtex_key = models.CharField(max_length=160, unique=True)
    bibtex_raw = models.TextField(blank=True)
    entry_type = models.CharField(
        max_length=40, blank=True, help_text=_("book, article, incollection, …")
    )
    title = models.CharField(max_length=500, blank=True)
    authors = models.CharField(max_length=500, blank=True)
    year = models.IntegerField(null=True, blank=True)
    citation_din = models.TextField(blank=True, help_text=_("Cached DIN-style citation."))
    url = models.URLField(blank=True)
    doi = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ["authors", "year"]

    def __str__(self):
        return self.citation_din or self.bibtex_key


# ---------------------------------------------------------------------------
# Core entity: the artefact
# ---------------------------------------------------------------------------
class ObjectCategory(models.TextChoices):
    STAMP_SEAL = "stamp_seal", _("Stamp seal")
    CYLINDER_SEAL = "cylinder_seal", _("Cylinder seal")
    SEAL_IMPRESSION = "seal_impression", _("Seal impression / bulla")
    JAR_HANDLE_IMPRESSION = "jar_handle_impression", _("Jar-handle impression")
    SCARAB = "scarab", _("Scarab / scaraboid")
    MONUMENTAL = "monumental_inscription", _("Monumental inscription")
    OTHER = "other", _("Other")


class Condition(models.TextChoices):
    INTACT = "intact", _("Intact")
    FRAGMENTARY = "fragmentary", _("Fragmentary")
    WORN = "worn", _("Worn")
    DAMAGED = "damaged", _("Damaged")
    UNKNOWN = "unknown", _("Unknown")


class Artefact(OrganizationOwnedModel, TimeStampedModel):
    """A seal, sealing, cylinder seal, jar-handle impression or inscription.

    Almost every field is optional on purpose: the survey records whatever is
    known and the rest is filled in later. ``uuid`` gives a stable, citable
    permalink independent of the title or database id.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    title = models.CharField(max_length=255)

    category = models.CharField(
        max_length=40, choices=ObjectCategory.choices, default=ObjectCategory.STAMP_SEAL
    )
    object_type = models.ForeignKey(
        ObjectType, null=True, blank=True, on_delete=models.SET_NULL, related_name="artefacts"
    )

    # Find context
    findspot = models.ForeignKey(
        Findspot, null=True, blank=True, on_delete=models.SET_NULL, related_name="artefacts"
    )
    find_context = models.ForeignKey(
        StratigraphicContext, null=True, blank=True, on_delete=models.SET_NULL, related_name="artefacts"
    )
    region = models.ForeignKey(
        Region, null=True, blank=True, on_delete=models.SET_NULL, related_name="artefacts",
        help_text=_("Region of the find (denormalised for faceting)."),
    )

    # Current keeping
    repository = models.ForeignKey(
        Repository, null=True, blank=True, on_delete=models.SET_NULL, related_name="artefacts"
    )

    # Dating: archaeological (period) may conflict with epigraphic (dating_text).
    period = models.ForeignKey(
        Period, null=True, blank=True, on_delete=models.SET_NULL, related_name="artefacts"
    )
    dating_text = models.CharField(
        max_length=255, blank=True, help_text=_("Free dating note, e.g. epigraphic date or a conflict.")
    )
    ruler = models.CharField(
        max_length=255, blank=True, help_text=_("Associated ruler / dynasty, if identifiable.")
    )

    # Origin (may differ from find spot — used for trade-route / workshop analysis)
    origin_region = models.ForeignKey(
        Region, null=True, blank=True, on_delete=models.SET_NULL, related_name="artefacts_originating"
    )
    origin_note = models.CharField(max_length=255, blank=True)

    # Quick flags for faceting
    is_inscribed = models.BooleanField(default=False)
    has_iconography = models.BooleanField(default=True)
    is_published = models.BooleanField(
        default=True, help_text=_("Visible on the public catalogue.")
    )

    condition = models.CharField(
        max_length=20, choices=Condition.choices, default=Condition.UNKNOWN, blank=True
    )
    preservation_note = models.TextField(blank=True)

    # Relations
    materials = models.ManyToManyField(Material, blank=True, related_name="artefacts")
    iconographic_features = models.ManyToManyField(
        IconographicMotif, blank=True, related_name="artefacts"
    )
    publications = models.ManyToManyField(
        Publication, through="PublicationReference", blank=True, related_name="artefacts"
    )

    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    tags = TaggableManager(blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "artefact"
            self.slug = f"{base}-{self.uuid.hex[:8]}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:artefact-detail", kwargs={"slug": self.slug})

    @property
    def primary_image(self):
        return self.media.filter(is_primary=True).first() or self.media.first()


class Identifier(models.Model):
    """Inventory / catalogue numbers; an artefact can carry several schemes."""

    artefact = models.ForeignKey(
        Artefact, on_delete=models.CASCADE, related_name="identifiers"
    )
    scheme = models.CharField(
        max_length=120, help_text=_("e.g. 'IAA', 'Museum no.', 'CSSL', 'Corpus Keel'.")
    )
    value = models.CharField(max_length=255)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_primary", "scheme"]

    def __str__(self):
        return f"{self.scheme}: {self.value}"


class Measurement(models.Model):
    """A single measured dimension. Multiple per artefact; sources may disagree."""

    class Kind(models.TextChoices):
        HEIGHT = "height", _("Height")
        WIDTH = "width", _("Width")
        THICKNESS = "thickness", _("Thickness")
        DIAMETER = "diameter", _("Diameter")
        LENGTH = "length", _("Length")
        WEIGHT = "weight", _("Weight")

    artefact = models.ForeignKey(
        Artefact, on_delete=models.CASCADE, related_name="measurements"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    value = models.DecimalField(max_digits=10, decimal_places=3)
    unit = models.CharField(max_length=20, default="mm")
    method = models.CharField(max_length=120, blank=True, help_text=_("caliper, estimated, …"))
    source = models.ForeignKey(
        Publication, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    def __str__(self):
        return f"{self.get_kind_display()}: {self.value} {self.unit}"


class MaterialAnalysis(models.Model):
    """Scientific material analysis (chemical composition, provenance)."""

    artefact = models.ForeignKey(
        Artefact, on_delete=models.CASCADE, related_name="material_analyses"
    )
    method = models.CharField(max_length=160, help_text=_("XRF, petrography, radiocarbon, …"))
    lab = models.CharField(max_length=255, blank=True)
    sample_id = models.CharField(max_length=120, blank=True)
    results = models.JSONField(null=True, blank=True)
    interpretation = models.TextField(blank=True, help_text=_("e.g. inferred origin / workshop."))
    source = models.ForeignKey(
        Publication, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        verbose_name_plural = "material analyses"

    def __str__(self):
        return f"{self.method} ({self.artefact})"


class MediaItem(models.Model):
    """An image, drawing, RTI, 3D model, IIIF manifest or PDF plate of an artefact."""

    class Kind(models.TextChoices):
        PHOTO = "photo", _("Photograph")
        DRAWING = "drawing", _("Drawing")
        RTI = "rti", _("RTI")
        MODEL_3D = "model_3d", _("3D model")
        IIIF = "iiif", _("IIIF manifest")
        PDF = "pdf", _("PDF / plate")
        OTHER = "other", _("Other")

    class View(models.TextChoices):
        OBVERSE = "obverse", _("Obverse")
        REVERSE = "reverse", _("Reverse")
        SIDE = "side", _("Side")
        IMPRESSION = "impression", _("Impression")
        MODERN_IMPRESSION = "modern_impression", _("Modern impression")
        DETAIL = "detail", _("Detail")
        OTHER = "other", _("Other")

    artefact = models.ForeignKey(Artefact, on_delete=models.CASCADE, related_name="media")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.PHOTO)
    view = models.CharField(max_length=20, choices=View.choices, blank=True)
    file = models.FileField(upload_to="catalog/media/", blank=True)
    iiif_manifest_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True, help_text=_("External image URL if not uploaded."))
    caption = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=255, blank=True)
    copyright_note = models.CharField(max_length=255, blank=True)
    license = models.CharField(max_length=120, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.caption or f"{self.get_kind_display()} of {self.artefact}"


# ---------------------------------------------------------------------------
# Epigraphy
# ---------------------------------------------------------------------------
class Inscription(OrganizationOwnedModel, TimeStampedModel):
    """An inscription on an artefact. A monument can carry several."""

    artefact = models.ForeignKey(
        Artefact, on_delete=models.CASCADE, related_name="inscriptions"
    )
    script = models.ForeignKey(
        ScriptType, null=True, blank=True, on_delete=models.SET_NULL, related_name="inscriptions"
    )
    language = models.ForeignKey(
        Language, null=True, blank=True, on_delete=models.SET_NULL, related_name="inscriptions"
    )
    technique = models.CharField(max_length=120, blank=True, help_text=_("incised, relief, …"))
    position = models.CharField(max_length=160, blank=True, help_text=_("e.g. 'around field', 'two registers'."))
    line_count = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"Inscription on {self.artefact}"

    @property
    def preferred_reading(self):
        return self.readings.filter(is_preferred=True).first() or self.readings.first()


class Reading(TimeStampedModel):
    """A reading variant of an inscription. Different scholars / sources read
    differently; ``is_preferred`` marks your working reading."""

    class Certainty(models.TextChoices):
        CERTAIN = "certain", _("Certain")
        PROBABLE = "probable", _("Probable")
        UNCERTAIN = "uncertain", _("Uncertain")
        PROPOSED = "proposed", _("Proposed / reconstructed")

    inscription = models.ForeignKey(
        Inscription, on_delete=models.CASCADE, related_name="readings"
    )
    reading_normalized = models.CharField(max_length=500, blank=True)
    reading_diplomatic = models.TextField(blank=True)
    transliteration = models.TextField(blank=True)
    translation_en = models.TextField(blank=True)
    certainty = models.CharField(
        max_length=20, choices=Certainty.choices, default=Certainty.PROBABLE
    )
    is_preferred = models.BooleanField(default=False)
    generated_by_model = models.BooleanField(
        default=False, help_text=_("Reading produced by an OCR / LLM pipeline.")
    )
    notes = models.TextField(blank=True)
    publications = models.ManyToManyField(Publication, blank=True, related_name="readings")
    history = HistoricalRecords()

    class Meta:
        ordering = ["-is_preferred", "certainty"]

    def __str__(self):
        return self.reading_normalized or f"Reading #{self.pk}"


# ---------------------------------------------------------------------------
# Provenance & bibliography links
# ---------------------------------------------------------------------------
class ProvenanceEvent(models.Model):
    """A station in the object's history: excavation, purchase, transfer, loan…"""

    class EventType(models.TextChoices):
        EXCAVATION = "excavation", _("Excavation")
        PURCHASE = "purchase", _("Purchase")
        TRANSFER = "transfer", _("Transfer")
        LOAN = "loan", _("Loan")
        COLLECTION = "collection", _("Collection")
        UNKNOWN = "unknown", _("Unknown")

    artefact = models.ForeignKey(
        Artefact, on_delete=models.CASCADE, related_name="provenance_events"
    )
    event_type = models.CharField(
        max_length=20, choices=EventType.choices, default=EventType.UNKNOWN
    )
    repository = models.ForeignKey(
        Repository, null=True, blank=True, on_delete=models.SET_NULL, related_name="provenance_events"
    )
    place = models.CharField(max_length=255, blank=True)
    date_text = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.get_event_type_display()} — {self.artefact}"


class PublicationReference(models.Model):
    """Through model linking an artefact to a publication, with the citation role."""

    class Role(models.TextChoices):
        EDITIO_PRINCEPS = "editio_princeps", _("Editio princeps")
        DISCUSSION = "discussion", _("Discussion")
        READING = "reading", _("Reading")
        ICONOGRAPHY = "iconography", _("Iconography")
        CATALOG = "catalog", _("Catalogue")
        MENTION = "mention", _("Mention")

    artefact = models.ForeignKey(
        Artefact, on_delete=models.CASCADE, related_name="publication_refs"
    )
    publication = models.ForeignKey(
        Publication, on_delete=models.CASCADE, related_name="artefact_refs"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.DISCUSSION)
    pages = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["role"]

    def __str__(self):
        return f"{self.publication} ({self.get_role_display()})"
