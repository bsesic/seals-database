"""Project published Django records onto the djangordf RDF models.

The relational models are the source of truth; this maps published artefacts
(and the vocabulary terms, places and periods they reference) onto the RDF
models with stable, dereferenceable IRIs, so re-running the sync overwrites
rather than duplicates triples.

The same builders serve two purposes:

* ``sync_*`` — persist to the configured triple store (idempotent).
* ``graph_for_*`` — build an rdflib ``Graph`` in memory (``save=False``) for
  content-negotiated RDF responses, without touching the store.
"""

from django.conf import settings
from djangordf import LangString
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import DCTERMS, FOAF, RDFS, SKOS

from catalog.models import Artefact
from catalog.rdf_models import Artefact as RDFArtefact
from catalog.rdf_models import Concept, Inscription, Period, Place, Reading

CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")


def _base():
    return settings.RDF_BASE_URI.rstrip("/")


def _gyear(year):
    # xsd:gYear: "0700" (CE) or "-0700" (BCE); no leading plus.
    return f"-{abs(year):04d}" if year < 0 else f"{year:04d}"


def _concept(cache, kind, term, save=True):
    iri = f"{_base()}/id/{kind}/{term.pk}"
    if iri in cache:
        return cache[iri]
    concept = Concept(iri=iri, pref_label=[LangString(term.label, "en")])
    if getattr(term, "skos_uri", ""):
        concept.exact_match = [URIRef(term.skos_uri)]
    parent = getattr(term, "broader", None) or getattr(term, "parent", None)
    if parent:
        concept.broader = [_concept(cache, kind, parent, save)]
    if save:
        concept.save()
    cache[iri] = concept
    return concept


def _place(cache, findspot, save=True):
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
    if save:
        place.save()
    cache[iri] = place
    return place


def _period(cache, period, save=True):
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
    if save:
        rdf_period.save()
    cache[iri] = rdf_period
    return rdf_period


def _inscription(cache, artefact_iri_str, ins, save=True):
    iri = f"{artefact_iri_str}/inscription/{ins.pk}"
    if iri in cache:
        return cache[iri]
    rins = Inscription(iri=iri)
    if ins.script:
        rins.script = ins.script.label
    if ins.language:
        rins.language = ins.language.label
    readings = []
    preferred = None
    for r in ins.readings.all():
        r_iri = f"{iri}/reading/{r.pk}"
        rr = Reading(iri=r_iri)
        if r.reading_normalized:
            rr.content = r.reading_normalized
        if r.transliteration:
            rr.transliteration = r.transliteration
        if r.translation_en:
            rr.translation = [LangString(r.translation_en, "en")]
        note = f"certainty: {r.get_certainty_display()}"
        if r.is_preferred:
            note += " (preferred)"
        rr.certainty = note
        if save:
            rr.save()
        cache[r_iri] = rr
        readings.append(rr)
        if r.reading_normalized and (r.is_preferred or preferred is None):
            preferred = r.reading_normalized
    if readings:
        rins.has_reading = readings
    if preferred:
        rins.content = preferred
    if save:
        rins.save()
    cache[iri] = rins
    return rins


def artefact_iri(artefact):
    return f"{_base()}{artefact.get_absolute_url()}"


def build_artefact(artefact, cache, save=True):
    """Build (and optionally persist) the RDF representation of one artefact.

    Returns the RDFArtefact instance; ``cache`` collects the referenced
    Concept / Place / Period instances so a caller can serialize them too.
    """
    ra = RDFArtefact(
        iri=artefact_iri(artefact),
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
        ra.has_type = _concept(cache, "object-type", artefact.object_type, save)
    materials = [_concept(cache, "material", m, save) for m in artefact.materials.all()]
    if materials:
        ra.consists_of = materials
    motifs = [
        _concept(cache, "motif", m, save)
        for m in artefact.iconographic_features.all()
    ]
    if motifs:
        ra.subject = motifs
    if artefact.region:
        ra.spatial = _concept(cache, "region", artefact.region, save)
    if artefact.findspot:
        ra.location = _place(cache, artefact.findspot, save)
    if artefact.period:
        ra.temporal = _period(cache, artefact.period, save)

    inscriptions = [
        _inscription(cache, ra.iri, ins, save)
        for ins in artefact.inscriptions.all()
    ]
    if inscriptions:
        ra.carries = inscriptions

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

    if save:
        ra.save()
    return ra


def sync_artefact(artefact, cache=None):
    """Create or overwrite the RDF representation of one artefact in the store."""
    return build_artefact(artefact, {} if cache is None else cache, save=True)


def _published_queryset():
    return (
        Artefact.objects.filter(is_published=True)
        .select_related("object_type", "region", "period", "findspot")
        .prefetch_related(
            "identifiers", "materials", "iconographic_features", "media",
            "inscriptions__script", "inscriptions__language", "inscriptions__readings",
        )
    )


def sync_all():
    """Sync every published artefact. Returns the number of artefacts synced."""
    cache = {}
    count = 0
    for artefact in _published_queryset():
        build_artefact(artefact, cache, save=True)
        count += 1
    return count


def prune_stale():
    """Remove RDF artefacts whose Django source is no longer published/present.

    Returns the number of artefact resources deleted. Shared vocabulary
    concepts are kept (they are stable and harmless if unreferenced).
    """
    expected = {artefact_iri(a) for a in Artefact.objects.filter(is_published=True)}
    deleted = 0
    for existing in RDFArtefact.objects.all():
        if str(existing.iri) not in expected:
            existing.delete()
            deleted += 1
    return deleted


# --- In-memory graph building (for content-negotiated RDF responses) -------
def _bind_prefixes(g):
    g.bind("crm", CRM)
    g.bind("skos", SKOS)
    g.bind("dcterms", DCTERMS)
    g.bind("geo", GEO)
    g.bind("foaf", FOAF)
    g.bind("rdfs", RDFS)


def _graph_from(instances):
    g = Graph()
    _bind_prefixes(g)
    for obj in instances:
        for triple in obj._to_triples():
            g.add(triple)
    return g


def graph_for_artefact(artefact):
    cache = {}
    ra = build_artefact(artefact, cache, save=False)
    return _graph_from(list(cache.values()) + [ra])


def graph_for_dataset(artefacts=None):
    if artefacts is None:
        artefacts = _published_queryset()
    cache = {}
    artefact_instances = [build_artefact(a, cache, save=False) for a in artefacts]
    return _graph_from(list(cache.values()) + artefact_instances)


# Serialization format -> (rdflib format, content type).
RDF_FORMATS = {
    "turtle": ("turtle", "text/turtle"),
    "ttl": ("turtle", "text/turtle"),
    "jsonld": ("json-ld", "application/ld+json"),
    "json-ld": ("json-ld", "application/ld+json"),
    "xml": ("xml", "application/rdf+xml"),
    "rdf": ("xml", "application/rdf+xml"),
    "nt": ("nt", "application/n-triples"),
}


def negotiate_format(request):
    """Pick an RDF format from ?format= or the Accept header (default turtle)."""
    requested = request.GET.get("format", "").lower()
    if requested in RDF_FORMATS:
        return RDF_FORMATS[requested]
    accept = request.META.get("HTTP_ACCEPT", "")
    for key, spec in RDF_FORMATS.items():
        if spec[1] in accept:
            return spec
    return RDF_FORMATS["turtle"]
