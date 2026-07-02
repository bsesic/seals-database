# Catalog data model

The `catalog` app holds the research data for the *Southern Levantine Stamp
Seals & Bullae* corpus (Iron IIC → Persian period). It is **relational-first**
for the survey, structured so an **RDF / SPARQL** layer (Apache Jena Fuseki) and
a **CIDOC-CRM / SKOS** mapping can be added later without reshaping the tables.

## Tiers

**Controlled vocabularies & shared reference data** (global lookup tables, each
with an optional `skos_uri` / external URI for Linked Open Data alignment, e.g.
with the CSSL corpus):

- `ObjectType`, `Material`, `ScriptType`, `Language`, `IconographicMotif`
  (hierarchical via `broader`), `Region` (hierarchical via `parent`)
- `PeriodScheme` → `Period` (years as integers, BCE negative)
- `Repository`, `Findspot`, `Excavation` → `StratigraphicContext`
- `Publication` (BibTeX-first: `bibtex_raw` is the source of truth)

**Tenant-owned records** (inherit `OrganizationOwnedModel`, like the boilerplate
`documents` app — solo survey = your personal organization, multi-user later):

- `Artefact` — the core entity. Almost every field is optional by design.
  Stable citable permalink via `uuid` + `slug`. `category` (coarse, for facets)
  vs `object_type` (fine, controlled). Versioned with `django-simple-history`.
- `Inscription` (versioned) → `Reading` (variant readings, `is_preferred`,
  `certainty`, `generated_by_model` for OCR/LLM output; versioned)
- `Identifier`, `Measurement`, `MaterialAnalysis`, `MediaItem`
  (photo/drawing/RTI/3D/IIIF/PDF), `ProvenanceEvent`
- `PublicationReference` (through `Artefact`↔`Publication` with a citation role)

## Design choices

- **Optional everywhere**: only `title` (+ a default `category`) is effectively
  required, so the survey records partial data and backfills later.
- **Assertions vs truth**: `Measurement` and `Reading` can each carry their own
  `source` / `publications`, so conflicting values from different publications
  coexist instead of overwriting. Full per-field provenance (a `Statement` model)
  is a documented later step if conflicts pile up.
- **Versioning**: `simple_history` on `Artefact`, `Inscription`, `Reading` gives
  "rewind / who changed what", surfaced in the Unfold admin.
- **Faceting-ready**: `category`, `region`, `period`, `script`, `language`,
  `is_inscribed`, `has_iconography`, `materials`, `iconographic_features`,
  `tags`.

## Planned RDF / CIDOC-CRM mapping (later)

| Model | CIDOC-CRM / standard |
|-------|----------------------|
| `Artefact` | `E22 Human-Made Object` |
| `Findspot` / `Region` | `E53 Place` (+ GeoSPARQL) |
| `Excavation` | `E7 Activity` |
| `Period` | `E4 Period` / `E52 Time-Span` |
| `MediaItem` | `E73 Information Object` + IIIF |
| `Inscription` / `Reading` | TEI / EpiDoc export |
| vocabularies | SKOS concepts (`skos_uri`) |

## Roadmap (after data entry starts)

1. Public list + detail views, find-spot map, IIIF viewer (Mirador/UV).
2. Faceted search (Postgres FTS first; Elasticsearch backend is pre-wired).
3. DRF endpoints + `drf-spectacular` schema; then RDF/SPARQL export & Fuseki sync.
4. BibTeX import → parse into `Publication` fields + cached DIN citation.
5. Bookmarks, sharing, citation, relationship-graph view, statistics dashboards.
