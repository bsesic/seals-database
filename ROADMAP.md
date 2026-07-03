# Roadmap

Living plan for the **Django SaaS Boilerplate** — a templates-first Django monorepo
(backend + frontend + later mobile) cloned to start new SaaS platforms fast.

Each item maps to a GitHub Issue labelled with the matching `phase-N` tag. Items are checked
off here and the corresponding issue is closed when its branch is merged into `development`.

Architecture, package choices, and rationale: see [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md).

---

## Phase 1 — Foundation

Repo hygiene, monorepo migration, dev tooling, CI.

- [x] Initialize git repo, `.gitignore`, baseline commit; dissolve `frontend/.git`
- [x] Move Django backend into `backend/`
- [x] Fix landmines: set `AUTH_USER_MODEL`, use `get_user_model()` in serializers, drop SQLite db
- [x] Monolithic `core/settings.py` with `django-environ` + `if not DEBUG:` hardening block
- [x] `.env.example` with all variables documented (subsystem-grouped)
- [x] Switch default DB to PostgreSQL
- [x] `docker-compose.yml` for local dev (Postgres, Redis, Mailpit, web)
- [x] `.flake8` (max-line-length 100, ignore E203/W503, exclude migrations) + black
- [x] pytest + pytest-django + `conftest.py` fixtures + coverage
- [x] `.pre-commit-config.yaml` (hooks + flake8 + local pytest)
- [x] Two-file requirements split (`requirements.txt` + `requirements-dev.txt`)
- [x] GitHub Actions CI: check → makemigrations --check → flake8 → pytest (postgres + redis services)

## Phase 2 — Auth & User

- [x] django-allauth (session-based, template UI)
- [x] Social auth: Google, Microsoft, Apple, Facebook
- [x] 2FA via `allauth.mfa`
- [x] User profile view + edit (crispy-forms + Bootstrap)
- [x] Password reset flow
- [x] Email verification + welcome + login-notification templates
- [x] Separate transactional vs. marketing email (backends/tags)

## Phase 3 — Multi-tenancy & Teams

- [x] `Organization` model as the central unit
- [x] `Membership` with roles (Owner, Admin, Member)
- [x] Current-org middleware + org-scoped queryset manager
- [x] Team invitation flow (email + signed token)
- [x] All tenant-scoped views auto-filtered to the current organization
- [x] Subscriptions attach to Org, not User <!-- anchor in place; billing in Phase 5 -->

## Phase 4 — Frontend base (templates-first)

- [x] Bootstrap 5 + Vite asset pipeline (SCSS/JS) wired into Django templates
- [x] Base layout: header, footer, main nav, footer nav, social nav
- [x] i18n: language switcher + Django `gettext` + locale middleware
- [x] Cookie consent banner
- [x] Pagination partial/component
- [x] crispy-forms standard form rendering
- [x] Separate SEO-optimized marketing app: Home, About, FAQ, Imprint, Privacy, Terms, Contact
- [x] Error pages: 404, 500, maintenance

## Phase 5 — Billing (Stripe-only, low priority)

- [x] Stripe Checkout (subscribe) + Customer Portal (change/cancel)
- [x] Pricing page
- [x] Subscription management page
- [x] Billing page (payment method, billing address, history) <!-- via Stripe Customer Portal -->
- [x] Webhook handling with idempotency
- [x] VAT handling via Stripe Tax (VIES, reverse-charge)
- [x] Invoices via Stripe <!-- via Customer Portal -->

> **Boilerplate is production-usable from here (MVP cut).**

## Phase 6 — Features (per-project, opt-in)

- [x] Search: Postgres FTS default, Elasticsearch opt-in
- [x] File upload (images + docs) via django-storages object backend
- [x] django-taggit tagging/taxonomy
- [x] django-simple-history audit log
- [x] django-activity-stream activity feed
- [x] In-app notifications
- [x] django-fsm state machines <!-- via django-fsm-2 -->
- [x] django-import-export (CSV/Excel)
- [x] django-waffle feature flags
- [x] Newsletter subscribe/unsubscribe (provider API per project)

## Phase 7 — Security & Compliance

- [x] django-ratelimit on auth endpoints and API
- [x] GDPR data export (JSON download)
- [x] GDPR account deletion: soft-delete + hard-delete cron
- [x] Accessibility audit (Axe/Lighthouse) <!-- checklist in docs/accessibility.md -->
- [x] SEO: sitemap, robots.txt, meta tags, Open Graph
- [x] Privacy-friendly analytics (Plausible or Matomo)

## Phase 8 — REST API (deferred half of templates-first)

- [x] Django REST Framework API layer
- [x] `allauth.headless` + token flow for SPA/mobile
- [x] OpenAPI/Swagger docs (drf-spectacular)
- [x] Rate limiting + versioning + pagination standards

## Phase 9 — Admin polish

- [x] django-unfold admin theme
- [x] Flower (or rq dashboard) for background jobs <!-- Celery wired + Flower systemd unit -->

## Phase 10 — Deployment infrastructure

Deploys to benni's own server; always the current release from `main`.

- [x] Production multi-stage Dockerfile (non-root user)
- [x] `docker-compose.prod.yml` (Gunicorn or Daphne + Celery + Beat)
- [x] NGINX site template (TLS, static/media, `/ws/` upgrade, gzip, HSTS, proxy headers)
- [x] systemd units with hardening (Daphne/Gunicorn, Celery, Beat)
- [x] Postgres + Redis (cache + broker) wiring
- [x] Email via SMTP relay
- [x] `deploy.sh`: fetch release → deps → check --deploy → migrate → collectstatic → restart → `/readyz` healthcheck
- [x] Init step for migrations + collectstatic
- [x] Log rotation (`deploy/logrotate/saas-boilerplate`)
- [x] Sentry integration
- [x] Health endpoints `/healthz`, `/readyz`
- [x] Backup cron (pg_dump → restic → B2) + restore guide
- [x] CI/CD: build → push image to GHCR → SSH deploy (`.github/workflows/deploy.yml`)
- [x] Live deploy test on the server (operational; needs server + secrets)

## Phase 11 — Documentation

- [x] README with quickstart
- [x] "Start a new project from the boilerplate" step-by-step guide
- [x] Architecture Decision Records (ADRs)
- [x] Deployment runbook
- [x] Troubleshooting guide
- [x] CHANGELOG (Keep a Changelog format)

## Optional / later

- [ ] Wagtail as an opt-in module
- [ ] Cache admin UI
- [ ] Multi-region deployment (only under real load)
