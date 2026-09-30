"""Project published Django records onto the djangordf RDF models.

The relational models are the source of truth; this maps published artefacts
(and the vocabulary terms, places and periods they reference) onto the RDF
models with stable, dereferenceable IRIs, so re-running the sync overwrites
rather than duplicates triples.
"""

from django.conf import settings
from djangordf import LangString
from rdflib import URIRef

from catalog.models import Artefact
from catalog.rdf_models import Artefact as RDFArtefact
from catalog.rdf_models import Concept, Period, Place


def _base():
    return settings.RDF_BASE_URI.rstrip("/")


def _gyear(year):
    # xsd:gYear: "0700" (CE) or "-0700" (BCE); no leading plus.
    return f"-{abs(year):04d}" if year < 0 else f"{year:04d}"


def _concept(cache, kind, term):
    iri = f"{_base()}/id/{kind}/{term.pk}"
    if iri in cache:
        return cache[iri]
    concept = Concept(iri=iri, pref_label=[LangString(term.label, "en")])
    if getattr(term, "skos_uri", ""):
        concept.exact_match = [URIRef(term.skos_uri)]
    parent = getattr(term, "broader", None) or getattr(term, "parent", None)
    if parent:
        concept.broader = [_concept(cache, kind, parent)]
    concept.save()
    cache[iri] = concept
    return concept


def _place(cache, findspot):
    iri = f"{_base()}/id/findspot/{findspot.pk}"
    if iri in cache:
        return cache[iri]
    place = Place(iri=iri, label=findspot.name_modern)
    if findspot.name_ancient:
        place.alt_label = [LangString(findspot.name_ancient, "en")]
    if findspot.country:
        place.country = findspot.country
    if findspot.latitude is not None and findspot.longitude is not None:
        place.lat = str(findspot.latitude)
        place.long = str(findspot.longitude)
    if findspot.gazetteer_uri:
        place.exact_match = [URIRef(findspot.gazetteer_uri)]
    place.save()
    cache[iri] = place
    return place


def _period(cache, period):
    iri = f"{_base()}/id/period/{period.pk}"
    if iri in cache:
        return cache[iri]
    rdf_period = Period(iri=iri, pref_label=[LangString(period.label, "en")])
    if period.start_year is not None:
        rdf_period.begin = _gyear(period.start_year)
    if period.end_year is not None:
        rdf_period.end = _gyear(period.end_year)
    if period.skos_uri:
        rdf_period.exact_match = [URIRef(period.skos_uri)]
    rdf_period.save()
    cache[iri] = rdf_period
    return rdf_period


def sync_artefact(artefact, cache=None):
    """Create or overwrite the RDF representation of one artefact."""
    cache = {} if cache is None else cache
    iri = f"{_base()}{artefact.get_absolute_url()}"
    ra = RDFArtefact(
        iri=iri,
        label=artefact.title,
        title=artefact.title,
        category=artefact.get_category_display(),
        created=artefact.created_at.isoformat(),
        modified=artefact.updated_at.isoformat(),
    )
    if artefact.description:
        ra.description = artefact.description
    if artefact.dating_text:
        ra.dating = artefact.dating_text
    identifiers = [f"{i.scheme}: {i.value}" for i in artefact.identifiers.all()]
    if identifiers:
        ra.identifier = identifiers

    if artefact.object_type:
        ra.has_type = _concept(cache, "object-type", artefact.object_type)
    materials = [_concept(cache, "material", m) for m in artefact.materials.all()]
    if materials:
        ra.consists_of = materials
    motifs = [_concept(cache, "motif", m) for m in artefact.iconographic_features.all()]
    if motifs:
        ra.subject = motifs
    if artefact.region:
        ra.spatial = _concept(cache, "region", artefact.region)
    if artefact.findspot:
        ra.location = _place(cache, artefact.findspot)
    if artefact.period:
        ra.temporal = _period(cache, artefact.period)

    contents = [
        r.reading_normalized
        for ins in artefact.inscriptions.all()
        for r in ins.readings.all()
        if r.reading_normalized
    ]
    if contents:
        ra.symbolic_content = contents

    depiction, representation = [], []
    for media in artefact.media.all():
        if media.iiif_manifest_url:
            representation.append(URIRef(media.iiif_manifest_url))
        elif media.image_url:
            depiction.append(URIRef(media.image_url))
    if depiction:
        ra.depiction = depiction
    if representation:
        ra.representation = representation

    ra.save()
    return ra


def _published_queryset():
    return (
        Artefact.objects.filter(is_published=True)
        .select_related("object_type", "region", "period", "findspot")
        .prefetch_related(
            "identifiers", "materials", "iconographic_features", "media",
            "inscriptions__readings",
        )
    )


def sync_all():
    """Sync every published artefact. Returns the number of artefacts synced."""
    cache = {}
    count = 0
    for artefact in _published_queryset():
        sync_artefact(artefact, cache)
        count += 1
    return count
