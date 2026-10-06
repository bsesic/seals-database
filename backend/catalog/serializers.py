"""DRF serializers for the public catalogue API (read-only).

Compact list representation + a rich detail representation with nested media,
inscriptions/readings, measurements, provenance and bibliography. Controlled
vocabularies expose ``skos_uri`` so consumers (e.g. the CSSL corpus) can align
terms as Linked Open Data.
"""

from rest_framework import serializers

from catalog.models import (
    Artefact,
    Findspot,
    IconographicMotif,
    Identifier,
    Inscription,
    Material,
    Measurement,
    MediaItem,
    ObjectType,
    Period,
    ProvenanceEvent,
    PublicationReference,
    Reading,
    Region,
    ScriptType,
)


# ---- Controlled vocabularies ----------------------------------------------
class TermSerializer(serializers.ModelSerializer):
    """Flat vocabulary term (ObjectType, Material, ScriptType)."""

    class Meta:
        model = ObjectType  # overridden per viewset via `Meta.model`
        fields = ("id", "label", "description", "skos_uri")


class MaterialSerializer(TermSerializer):
    class Meta(TermSerializer.Meta):
        model = Material


class ScriptTypeSerializer(TermSerializer):
    class Meta(TermSerializer.Meta):
        model = ScriptType


class ObjectTypeSerializer(TermSerializer):
    class Meta(TermSerializer.Meta):
        model = ObjectType


class MotifSerializer(serializers.ModelSerializer):
    class Meta:
        model = IconographicMotif
        fields = ("id", "label", "broader", "skos_uri")


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ("id", "label", "parent", "skos_uri")


class PeriodSerializer(serializers.ModelSerializer):
    scheme = serializers.CharField(source="scheme.name", read_only=True)

    class Meta:
        model = Period
        fields = ("id", "label", "scheme", "start_year", "end_year", "skos_uri")


class FindspotSerializer(serializers.ModelSerializer):
    region = serializers.CharField(source="region.label", default=None, read_only=True)
    artefact_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Findspot
        fields = (
            "id", "name_modern", "name_ancient", "region", "country",
            "latitude", "longitude", "gazetteer_uri", "artefact_count",
        )


# ---- Artefact sub-objects -------------------------------------------------
class IdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Identifier
        fields = ("scheme", "value", "is_primary")


class MeasurementSerializer(serializers.ModelSerializer):
    kind = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = Measurement
        fields = ("kind", "value", "unit", "method")


class MediaItemSerializer(serializers.ModelSerializer):
    kind = serializers.CharField(source="get_kind_display", read_only=True)
    view = serializers.CharField(source="get_view_display", read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = MediaItem
        fields = (
            "kind", "view", "url", "iiif_manifest_url", "caption",
            "source", "copyright_note", "license",
        )

    def get_url(self, obj) -> str | None:
        request = self.context.get("request")
        if obj.file:
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return obj.image_url or None


class ReadingSerializer(serializers.ModelSerializer):
    certainty = serializers.CharField(source="get_certainty_display", read_only=True)

    class Meta:
        model = Reading
        fields = (
            "reading_normalized", "reading_diplomatic", "transliteration",
            "translation_en", "certainty", "is_preferred", "generated_by_model",
        )


class InscriptionSerializer(serializers.ModelSerializer):
    script = serializers.CharField(source="script.label", default=None, read_only=True)
    language = serializers.CharField(source="language.label", default=None, read_only=True)
    readings = ReadingSerializer(many=True, read_only=True)

    class Meta:
        model = Inscription
        fields = ("script", "language", "technique", "position", "line_count", "readings")


class ProvenanceEventSerializer(serializers.ModelSerializer):
    event_type = serializers.CharField(source="get_event_type_display", read_only=True)
    repository = serializers.CharField(source="repository.name", default=None, read_only=True)

    class Meta:
        model = ProvenanceEvent
        fields = ("event_type", "repository", "place", "date_text", "description")


class PublicationRefSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="get_role_display", read_only=True)
    citation = serializers.CharField(source="publication.__str__", read_only=True)
    bibtex_key = serializers.CharField(source="publication.bibtex_key", read_only=True)

    class Meta:
        model = PublicationReference
        fields = ("role", "citation", "bibtex_key", "pages")


# ---- Artefact -------------------------------------------------------------
class ArtefactListSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="v1:artefact-detail", lookup_field="slug"
    )
    category = serializers.CharField(source="get_category_display", read_only=True)
    object_type = serializers.CharField(source="object_type.label", default=None, read_only=True)
    region = serializers.CharField(source="region.label", default=None, read_only=True)
    period = serializers.CharField(source="period.label", default=None, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    short_id = serializers.CharField(read_only=True)

    class Meta:
        model = Artefact
        fields = (
            "short_id", "slug", "url", "title", "category", "object_type",
            "region", "period", "dating_text", "is_inscribed", "has_iconography",
            "thumbnail", "updated_at",
        )

    def get_thumbnail(self, obj) -> str | None:
        img = obj.primary_image
        if not img:
            return None
        request = self.context.get("request")
        if img.file:
            return request.build_absolute_uri(img.file.url) if request else img.file.url
        return img.image_url or None


class ArtefactDetailSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="get_category_display", read_only=True)
    condition = serializers.CharField(source="get_condition_display", read_only=True)
    object_type = serializers.CharField(source="object_type.label", default=None, read_only=True)
    region = serializers.CharField(source="region.label", default=None, read_only=True)
    origin_region = serializers.CharField(
        source="origin_region.label", default=None, read_only=True
    )
    repository = serializers.CharField(source="repository.name", default=None, read_only=True)
    period = PeriodSerializer(read_only=True)
    findspot = FindspotSerializer(read_only=True)
    materials = serializers.SlugRelatedField(slug_field="label", many=True, read_only=True)
    iconographic_features = serializers.SlugRelatedField(
        slug_field="label", many=True, read_only=True
    )
    identifiers = IdentifierSerializer(many=True, read_only=True)
    measurements = MeasurementSerializer(many=True, read_only=True)
    media = MediaItemSerializer(many=True, read_only=True)
    inscriptions = InscriptionSerializer(many=True, read_only=True)
    provenance_events = ProvenanceEventSerializer(many=True, read_only=True)
    bibliography = PublicationRefSerializer(source="publication_refs", many=True, read_only=True)
    tags = serializers.SerializerMethodField()
    web_url = serializers.SerializerMethodField()
    short_id = serializers.CharField(read_only=True)

    class Meta:
        model = Artefact
        fields = (
            "short_id", "slug", "web_url", "title", "category", "object_type",
            "region", "findspot", "period", "dating_text", "ruler",
            "origin_region", "origin_note", "repository", "condition",
            "preservation_note", "is_inscribed", "has_iconography",
            "materials", "iconographic_features", "identifiers", "measurements",
            "media", "inscriptions", "provenance_events", "bibliography",
            "description", "notes", "tags", "created_at", "updated_at",
        )

    def get_tags(self, obj) -> list[str]:
        return [t.name for t in obj.tags.all()]

    def get_web_url(self, obj) -> str:
        request = self.context.get("request")
        url = obj.get_absolute_url()
        return request.build_absolute_uri(url) if request else url


class ArtefactWriteSerializer(serializers.ModelSerializer):
    """Writable representation for creating and editing artefacts via the API.

    Foreign keys and many-to-many relations are written by id; ``tags`` is a
    list of names. ``organization`` and ``created_by`` are set by the view, not
    the client. Nested children (inscriptions, media, measurements) are managed
    through the admin for now.
    """

    # write_only: tags are written from a list of names and rendered back in
    # to_representation (the model attribute is a TaggableManager, not a list).
    tags = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True,
        help_text="List of tag names.",
    )
    short_id = serializers.CharField(read_only=True)

    class Meta:
        model = Artefact
        fields = (
            "short_id", "slug", "title", "category", "object_type", "findspot",
            "find_context", "region", "repository", "period", "dating_text",
            "ruler", "origin_region", "origin_note", "is_inscribed",
            "has_iconography", "is_published", "condition", "preservation_note",
            "materials", "iconographic_features", "description", "notes",
            "tags", "created_at", "updated_at",
        )
        read_only_fields = ("short_id", "slug", "created_at", "updated_at")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["tags"] = [t.name for t in instance.tags.all()]
        return data

    def _save_tags(self, instance, tags):
        if tags is not None:
            instance.tags.set(tags, clear=True)

    def create(self, validated_data):
        tags = validated_data.pop("tags", None)
        instance = super().create(validated_data)
        self._save_tags(instance, tags)
        return instance

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        instance = super().update(instance, validated_data)
        self._save_tags(instance, tags)
        return instance
