# Implementation Plan — Django SaaS Boilerplate

> Concretized roadmap, tailored to the **current repo state**, a **monorepo** layout
> (backend + frontend + later mobile), and **benni's existing conventions** (mined from
> spielekiste, immobot, AlchemyPy, haskala, wagtail-common-base).
> Last updated: 2026-06-03. Living document — decisions here become ADRs (Phase 11).

---

## 0. Current state

**Backend** (`core/`, `users/`)
- Django 5.1.4, DRF 3.15, SimpleJWT, corsheaders.
- Custom `User` model present, **but `AUTH_USER_MODEL` is NOT set** → landmine.
- `users/serializers.py` imports `django.contrib.auth.models.User` instead of the custom one.
- One endpoint (`/api/users/profile/`). **SQLite**, single settings file, no `.env`, hardcoded `SECRET_KEY`/`DEBUG=True`.

**Frontend** (`frontend/`)
- Vue 3 SPA (vuex, vue-router, axios), built with deprecated `@vue/cli-service`.
- Has its own `.git` (a mistake/test) → dissolve for the monorepo.

**Mobile**: `android/`, `react-native/`, `swift/` (one level up) — empty, deferred.

---

## 1. Architecture decisions (locked)

| # | Decision | Choice |
|---|----------|--------|
| 1.1 | UI rendering | **Templates-first**: server-rendered Django + Bootstrap is the primary UI. The **DRF REST API comes later** (feeds Vue web + mobile). |
| 1.2 | Auth | **django-allauth** session-based now; `allauth.headless` + tokens later for API/mobile. Social: Google/Microsoft/Apple/Facebook; 2FA via `allauth.mfa`. |
| 1.3 | Multi-tenancy | **Organization FK row-scoping** (manager + middleware). No django-tenants. |
| 1.4 | Billing | **Stripe only**, low priority — only for paid SaaS, beyond core boilerplate scope. |
| 1.5 | Settings | **Monolithic `core/settings.py`** with `django-environ` + `if not DEBUG:` hardening block (matches benni's repos). No base/dev/prod split. |
| 1.6 | Frontend build | **Vite** as the asset pipeline feeding Django templates (SCSS/JS); Vue for progressive enhancement; full SPA deferred with the API. Pinia over Vuex when SPA arrives. |
| 1.7 | Marketing/legal/SEO pages (D-1) | **Separate**, server-rendered for SEO, easy to manage (own Django app `pages`/`marketing`). |
| 1.8 | Repo layout (D-5) | Django backend lives in `backend/` subdir of the monorepo. |
| 1.9 | Lint/format | **flake8** (`max-line-length=100`, ignore E203/W503, exclude migrations) + black formatting. pytest + pytest-django. |

**Deviations from the original brainstorm roadmap**, all confirmed with benni:
- Brainstorm said API-first (Phase 4 templates were contradictory) → **templates-first** is the explicit choice; API moved later.
- Brainstorm said `django-payments` (Stripe/PayPal/Klarna) → **Stripe-only**, deprioritized.
- Brainstorm implied ruff → **flake8** (benni's standard).
- vue-cli (EOL) → **Vite**.

---

## 2. Monorepo layout (target)

```
saas-boilerplate/                # git root (to be initialized)
├── backend/                     # Django root (move of core/ + users/)
│   ├── core/                    # settings.py (monolithic), urls, asgi, wsgi
│   ├── apps/                    # users, organizations, pages, api, ...
│   ├── templates/               # global templates
│   ├── static/                  # source static (built assets land here)
│   ├── manage.py
│   ├── conftest.py
│   ├── pyproject.toml           # black, pytest config
│   ├── .flake8
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/                    # Vite asset pipeline (Vue progressive); frontend/.git dissolved
├── deploy/                      # nginx, systemd units, deploy.sh, .env.production.example, docker-compose.prod.yml
├── docs/                        # this plan, ADRs, runbooks
├── docker-compose.yml           # local dev: postgres, redis, mailpit, web
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .github/workflows/ci.yml
├── ROADMAP.md
├── CHANGELOG.md
└── README.md
```

**Monorepo migration steps (Phase 1, step 0):**
1. `git init` at root; `.gitignore` (venv, node_modules, `*.sqlite3`, `.env`, `.DS_Store`, `__pycache__`, staticfiles, media).
2. Remove `frontend/.git` (history is just `init`, discard).
3. Move Django into `backend/`.
4. Baseline commit **before** any content changes.

---

## 3. Immediate fixes (landmines — before any real migration)

1. `AUTH_USER_MODEL = 'users.User'` in settings.
2. `users/serializers.py` → `get_user_model()`.
3. SQLite → **Postgres** (local via docker-compose).
4. `SECRET_KEY`/`DEBUG`/`ALLOWED_HOSTS` from `.env` via django-environ.
5. Drop the throwaway `db.sqlite3` + initial migrations, regenerate clean.

---

## 4. Phase plan

> Mirrors the brainstorm phases, re-cut for templates-first. MVP cut after Phase 5.
> Each item maps to a GitHub issue labelled `phase-N` (see ROADMAP.md).

### Phase 1 — Foundation
Monorepo migration + immediate fixes. `django-environ` settings with hardening block.
`docker-compose.yml` (Postgres, Redis, Mailpit, web). flake8 + black + pytest + pytest-django +
pre-commit. Two-file requirements split. Git flow (`main`/`development`/`feature/*`/`bugfix/*`).
GitHub Actions CI (check → makemigrations --check → flake8 → pytest, with postgres+redis services).

### Phase 2 — Auth & User
django-allauth (session, template-based). Social providers (Google/Microsoft/Apple/Facebook).
2FA (`allauth.mfa`). Password reset, email verification, login notification. Transactional email
templates via SMTP relay. Profile view/edit (template forms with crispy-forms + Bootstrap).

### Phase 3 — Multi-tenancy & Teams
`Organization` + `Membership` (Owner/Admin/Member). Current-org middleware + scoped manager.
Invitation flow (email + signed token). Org-scoped views. Subscriptions attach to Org.

### Phase 4 — Frontend base (templates-first)
Bootstrap 5 + Vite asset pipeline (django-vite or manifest). Base layout (header/footer/nav).
i18n (Django `gettext`, language switcher, locale middleware). Cookie banner. Pagination partial.
crispy-forms standard form rendering. Error pages (404/500/maintenance).
**Marketing/legal pages live in a separate, SEO-optimized app (D-1).**

### Phase 5 — Billing (Stripe-only, low priority)
Stripe Checkout (subscribe) + Customer Portal (change/cancel/billing). Optional dj-stripe sync.
Pricing page. Webhooks with idempotency. Stripe Tax for VAT/reverse-charge. Stripe invoices.
→ **End of MVP cut.**

### Phase 6 — Features (per-project, opt-in)
Postgres FTS (default) / Elasticsearch (opt-in). File upload via django-storages (R2/B2/Hetzner).
django-taggit, django-simple-history (audit), django-activity-stream, in-app notifications,
django-fsm, django-import-export, django-waffle (feature flags). CRUD = class-based views +
crispy-forms templates.

### Phase 7 — Security & Compliance
django-ratelimit on auth/API. GDPR data export (JSON). Account deletion (soft + hard-delete cron).
A11y audit (Axe/Lighthouse). SEO (sitemap, robots.txt, meta/OG). Privacy analytics (Plausible/Matomo).

### Phase 8 — REST API
DRF API layer (the deferred half of 1.1). `allauth.headless` + token flow for SPA/mobile.
drf-spectacular (OpenAPI/Swagger). Rate limiting. Versioning + pagination standards.

### Phase 9 — Admin polish
django-unfold admin theme. Flower for Celery monitoring.

### Phase 10 — Deployment infrastructure
Based on benni's proven configs:
- **NGINX** (immobot prod template): HTTP→HTTPS, TLS, static/media caching, `/ws/` upgrade, proxy headers, gzip, HSTS.
- **App server**: Daphne (ASGI) if Channels/WebSockets; otherwise Gunicorn (WSGI). systemd units with hardening (`ProtectSystem=strict`, `NoNewPrivileges`, `EnvironmentFile`).
- **Postgres** + **Redis** (cache + Celery broker) as shared services.
- **Email** via SMTP relay (Brevo/Postmark/SES).
- **Celery worker + beat** as separate services.
- **Docker**: multi-stage Dockerfile (non-root), `docker-compose.prod.yml`.
- **deploy.sh** (AlchemyPy pattern): fetch+reset to release tag/branch, deps, `check --deploy`, migrate, collectstatic, compilemessages, clearsessions, restart services, `/readyz` healthcheck with rollback.
- Sentry; `/healthz` + `/readyz` endpoints. Two-phase backward-compatible migrations. Backups (pg_dump → restic → B2).
- **Always deploy the current release** from `main`.

### Phase 11 — Documentation
README quickstart, "start a new project from the boilerplate" guide, ADRs (from §1), deployment
runbook, troubleshooting guide. CHANGELOG (Keep a Changelog format).

### Optional / later
Wagtail (opt-in CMS), cache admin UI, multi-region.

---

## 5. Dependency order

```
Phase 1 ─► Phase 2 ─┬─► Phase 3 ─► Phase 5 (Billing) ──► MVP
                    └─► Phase 4 ──┘
Phases 6,7,9: after MVP, per project need.
Phase 8 (API): the deferred API half; after templates are solid.
Phase 10 (Deploy): scaffolded early (benni asked for configs now), fully exercised at MVP.
Phase 11 (Docs): ongoing.
```

**Pragmatic principle:** build the boilerplate out of the next real project — Phases 1–4 as the
foundation, then pull reusable pieces back after each iteration.

---

## 6. Resolved open decisions

| ID | Decision | Resolution |
|----|----------|-----------|
| D-1 | Marketing/legal/SEO pages | Separate, server-rendered app; SEO-first, easy to manage |
| D-2 | Token strategy | Web = session cookie (allauth); Mobile = allauth tokens (Phase 8) |
| D-3 | PayPal | Not needed now; maybe per-app later, beyond core scope |
| D-4 | Vuex → Pinia | Yes (when the SPA/API phase arrives) |
| D-5 | Backend in `backend/` | Yes |
| D-6 | `stage` environment | Later; single `DEBUG`/`PRODUCTION` toggle for now |

---

## 7. Workflow conventions (apply to all work)

- **Branches**: `main` = releases + deploy; `development` = active dev; `feature/*`, `bugfix/*` for work. No auto-generated branch names.
- **Before every commit**: run tests + `flake8`. Commit only when green.
- **Commits/PRs/issues/comments**: English. No AI attribution anywhere.
- **Issues**: every roadmap item is a GitHub issue (`phase-N` label); close on merge.
