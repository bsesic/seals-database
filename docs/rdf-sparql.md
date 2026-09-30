# RDF, Linked Open Data & SPARQL

The catalogue is published as Linked Open Data using
[**djangordf**](https://github.com/bsesic/djangordf): declarative RDF models
that persist as triples in a SPARQL 1.1 triple store. The relational Django
models stay the source of truth; published records are projected onto the RDF
models with stable, dereferenceable IRIs.

## Mapping

`backend/catalog/rdf_models.py` maps the catalogue to CIDOC-CRM, SKOS, Dublin
Core Terms and WGS84:

| RDF model | Class | From |
|-----------|-------|------|
| `Artefact` | `crm:E22_Human-Made_Object` | `catalog.Artefact` (published) |
| `Concept`  | `skos:Concept` | object types, materials, motifs, regions |
| `Place`    | `crm:E53_Place` | find spots (with `geo:lat`/`geo:long`) |
| `Period`   | `crm:E4_Period` | periods (with `crm:P82a/P82b` begin/end) |

Vocabulary terms carry `skos:exactMatch` to their external `skos_uri`, so terms
can be aligned with the CSSL corpus and other LOD sources.

## Backends

Configured via `DJANGORDF_BACKEND` (see `core/settings.py`):

- **In-memory** (rdflib) — the default; used for development and tests.
- **Fuseki** — set `FUSEKI_ENDPOINT` (e.g. `http://localhost:3030/seals`) to
  sync to Apache Jena Fuseki over SPARQL 1.1. Fuseki then serves the public
  SPARQL endpoint. Optional `FUSEKI_USER` / `FUSEKI_PASSWORD`.

`RDF_BASE_URI` is the base for minted IRIs (an artefact's IRI is its web URL).

## Syncing

Project all published artefacts onto the triple store:

```bash
python manage.py sync_rdf
```

The sync is idempotent — stable IRIs mean re-running overwrites rather than
duplicates. Run it after data entry (or on a schedule / from `deploy.sh`).

## HTTP access (content negotiation)

Django serves RDF directly, so artefact IRIs are dereferenceable:

- `GET /catalog/<slug>/rdf/` — one artefact
- `GET /catalog/rdf/` — the whole published catalogue

Pick a format with `?format=turtle|jsonld|xml|nt` or the `Accept` header
(`text/turtle`, `application/ld+json`, `application/rdf+xml`,
`application/n-triples`); Turtle is the default. These responses are built
in memory from the mapping and do not require a triple store.

## Scheduled sync

`catalog.tasks.sync_rdf_task` (Celery) syncs and prunes; wire it to Celery beat
for a nightly refresh (see the task docstring). `manage.py sync_rdf --prune`
also removes artefacts that are no longer published.

## Running Fuseki

The production compose file (`deploy/docker-compose.prod.yml`) includes an
optional `fuseki` service with a persistent volume. Create a dataset named to
match `FUSEKI_ENDPOINT`, then run `sync_rdf`. Query it at
`<FUSEKI_ENDPOINT>/sparql`, e.g.:

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT ?artefact ?title WHERE {
  ?artefact a crm:E22_Human-Made_Object ; dcterms:title ?title .
} LIMIT 20
```

## Not yet done

- A richer inscription model (separate `crm:E34_Inscription` resources).
- Live verification against a running Fuseki instance.
