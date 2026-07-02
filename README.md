# SaaS Boilerplate

A templates-first Django monorepo for spinning up new SaaS platforms quickly.
Clone it, rename, and start building.

## Layout

```
backend/    Django project (templates-first; REST API comes later)
frontend/   Vite asset pipeline (Vue, progressive enhancement)
deploy/     NGINX, systemd units, deploy.sh, production compose
docs/       Implementation plan, ADRs, runbooks
```

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for architecture decisions
and [`ROADMAP.md`](ROADMAP.md) for the phased plan.

## Documentation

- [Start a new project from the boilerplate](docs/getting-started.md)
- [Architecture Decision Records](docs/adr/README.md)
- [Deployment runbook](docs/deployment-runbook.md) · [deploy reference](deploy/README.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Accessibility checklist](docs/accessibility.md)
- [Changelog](CHANGELOG.md)

## Quickstart (local development)

```bash
# 1. Start infrastructure (Postgres, Redis, Mailpit)
docker compose up -d db redis mailpit

# 2. Backend
cd backend
python -m venv ../venv && source ../venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # adjust if needed
python manage.py migrate
python manage.py runserver

# 3. Frontend assets (Vite). In a second terminal:
cd frontend
npm install
npm run dev            # dev server with HMR (django-vite picks it up when DEBUG=True)
# For a production build instead: npm run build  -> backend/static/dist/
```

The full stack (including the web container) can also run with `docker compose up`.

Mailpit UI: http://localhost:8025 · Vite dev server: http://localhost:5173

## Quality gates

Run before every commit (and enforced by pre-commit + CI):

```bash
cd backend
flake8 .
pytest
```

## Branching

- `main` — releases; deployed to production.
- `development` — active development.
- `feature/*`, `bugfix/*` — branched off `development`.

## Deployment

See [`deploy/README.md`](deploy/README.md). Always deploy the current release from `main`.
