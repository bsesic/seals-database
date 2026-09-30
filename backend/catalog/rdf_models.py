"""RDF model layer for the catalogue, built on djangordf.

These declarative ``RDFModel`` classes describe the catalogue in CIDOC-CRM (the
cultural-heritage reference ontology) plus SKOS, Dublin Core Terms and WGS84.
They persist as triples in the configured djangordf backend — an in-memory
rdflib store in development/tests, or Apache Jena Fuseki (SPARQL 1.1) in
production, which then serves the public SPARQL endpoint and can be aligned with
the CSSL corpus as Linked Open Data.

The relational Django models remain the source of truth; ``catalog.rdf_sync``
projects published records onto these RDF models with stable, dereferenceable
IRIs so re-syncing is idempotent.
"""

from djangordf import (
    DataProperty,
    LangStringProperty,
    ObjectProperty,
    RDFModel,
    URIProperty,
)
from rdflib import Namespace
from rdflib.namespace import DCTERMS, FOAF, RDFS, SKOS, XSD

CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")


class Concept(RDFModel):
    """A controlled-vocabulary term (object type, material, script, motif,
    region). Defaults to ``skos:Concept``; ``pref_label`` and ``broader`` use
    the SKOS convention predicates."""

    pref_label = LangStringProperty(many=True)
    broader = ObjectProperty("self", many=True)
    exact_match = URIProperty(predicate=SKOS.exactMatch, many=True)


class Place(RDFModel):
    """A find spot (crm:E53_Place) with an optional WGS84 position."""

    label = DataProperty(predicate=RDFS.label)
    alt_label = LangStringProperty(many=True)
    country = DataProperty(predicate=DCTERMS.spatial)
    lat = DataProperty(predicate=GEO.lat, datatype=XSD.decimal)
    long = DataProperty(predicate=GEO.long, datatype=XSD.decimal)
    exact_match = URIProperty(predicate=SKOS.exactMatch, many=True)

    class Meta:
        class_iri = "crm:E53_Place"


class Period(RDFModel):
    """A chronological period (crm:E4_Period) with begin/end years (BCE
    negative)."""

    pref_label = LangStringProperty(many=True)
    begin = DataProperty(predicate=CRM["P82a_begin_of_the_begin"], datatype=XSD.gYear)
    end = DataProperty(predicate=CRM["P82b_end_of_the_end"], datatype=XSD.gYear)
    exact_match = URIProperty(predicate=SKOS.exactMatch, many=True)

    class Meta:
        class_iri = "crm:E4_Period"


class Artefact(RDFModel):
    """A seal, sealing or inscription (crm:E22_Human-Made_Object)."""

    label = DataProperty(predicate=RDFS.label)
    title = DataProperty(predicate=DCTERMS.title)
    description = DataProperty(predicate=DCTERMS.description)
    category = DataProperty(predicate=DCTERMS.type)
    identifier = DataProperty(predicate=DCTERMS.identifier, many=True)
    dating = DataProperty(predicate=DCTERMS.date)
    created = DataProperty(predicate=DCTERMS.created, datatype=XSD.dateTime)
    modified = DataProperty(predicate=DCTERMS.modified, datatype=XSD.dateTime)

    has_type = ObjectProperty("Concept", predicate=CRM["P2_has_type"])
    consists_of = ObjectProperty("Concept", predicate=CRM["P45_consists_of"], many=True)
    subject = ObjectProperty("Concept", predicate=DCTERMS.subject, many=True)
    spatial = ObjectProperty("Concept", predicate=DCTERMS.spatial)
    location = ObjectProperty(
        "Place", predicate=CRM["P53_has_former_or_current_location"]
    )
    temporal = ObjectProperty("Period", predicate=DCTERMS.temporal)

    symbolic_content = DataProperty(
        predicate=CRM["P190_has_symbolic_content"], many=True
    )
    depiction = URIProperty(predicate=FOAF.depiction, many=True)
    representation = URIProperty(
        predicate=CRM["P138i_has_representation"], many=True
    )

    class Meta:
        class_iri = "crm:E22_Human-Made_Object"
