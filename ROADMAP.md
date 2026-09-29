# Roadmap

Project: **Seals Database** — a publication-oriented catalogue and knowledge graph
for inscribed stamp & cylinder seals, bullae, jar-handle impressions and
inscriptions from the Iron Age II to the Persian period in the Southern Levant.

Tasks are tracked as **GitHub Issues** (the single source of truth). This file is
a high-level overview; see the issues for detail and status.

## Branch & release model

- `main` — releases and deployment. We always deploy the current release from `main`.
- `development` — active development; feature/bugfix branches merge here.
- `feature/*`, `bugfix/*` (and other descriptive prefixes) — branched off `development`.
- Before every commit: run the tests and `flake8`.

## Done

- Catalogue data model (relational-first), admin, versioning — released.
- Public catalogue: list, detail with IIIF viewer, find-spot map (Leaflet).
- Faceted search (Postgres full-text search + multi-select facets).
- Read-only REST API (`/api/v1/`) with OpenAPI schema.
- Survey statistics dashboard.
- BibTeX import for the bibliography.

## Now — production deployment

Make the project production-ready and deployable on the server. → **[#8](../../issues/8)**
NGINX, Gunicorn (WSGI), PostgreSQL, Redis (cache + Celery broker), email (SMTP),
systemd services, Docker stack, backups, and CI/CD, all rebranded for this project.

## Next

- Rebrand the application UI to "Seals Database". → **[#9](../../issues/9)**
- Self-host front-end libraries (Mirador, Leaflet, Chart.js) via Vite, drop CDNs. → **[#10](../../issues/10)**
- Map: marker clustering and heatmap. → **[#11](../../issues/11)**
- REST API: authenticated write access. → **[#12](../../issues/12)**

## Later

- RDF/SPARQL export and Apache Jena Fuseki integration (CSSL / Linked Open Data). → **[#13](../../issues/13)**
- Wire the Elasticsearch search backend for the catalogue. → **[#14](../../issues/14)**
- 3D digitisation, feature detection and transcription (AI pipelines, per the exposé).
