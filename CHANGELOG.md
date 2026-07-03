# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Foundation** (Phase 1): monorepo layout (`backend/`, `frontend/`, `deploy/`, `docs/`),
  monolithic settings via django-environ with a production hardening block, PostgreSQL,
  local `docker-compose` (Postgres, Redis, Mailpit), flake8 + black + pytest + pre-commit,
  GitHub Actions CI, health probes `/healthz` and `/readyz`.
- **Auth & user** (Phase 2): django-allauth (email verification, password reset),
  social login (Google, Microsoft, Apple, Facebook), 2FA (allauth.mfa), profile
  view/edit, welcome and login-notification emails, transactional/marketing sender split.
- **Multi-tenancy & teams** (Phase 3): `Organization`, `Membership` (Owner/Admin/Member),
  `Invitation`; reusable `OrganizationOwnedModel`, scoping mixins, current-org middleware;
  invitations, member management, org switcher, auto personal org on signup.
- **Frontend base** (Phase 4): Bootstrap 5 via a Vite pipeline (django-vite), full layout
  partials, i18n (en/de) with a language switcher, cookie banner, pagination, a
  SEO-friendly marketing `pages` app, and error pages (404/500/maintenance).
- **Billing** (Phase 5): Stripe Checkout, Customer Portal, idempotent webhooks, Stripe Tax;
  subscription state on the organization; optional (disabled without keys).
- **Features** (Phase 6): `documents` (uploads via django-storages, tags, audit history,
  full-text search, import/export), in-app notifications, django-waffle feature flags.
- **Security & compliance** (Phase 7): rate limiting (django-ratelimit + allauth),
  GDPR data export and account deletion with a purge command, sitemap/robots,
  privacy-friendly analytics (Plausible/Matomo), accessibility checklist.
- **REST API** (Phase 8): versioned DRF API at `/api/v1/` (pagination, throttling,
  session + token auth), allauth.headless for SPA/mobile, OpenAPI docs via drf-spectacular.
- **Admin & jobs** (Phase 9): django-unfold admin theme, Celery wired into `core` with an
  example task, Flower monitoring.
- **Documentation** (Phase 11): getting-started guide, ADRs, deployment runbook,
  troubleshooting guide, this changelog.

### Deferred

- Elasticsearch search backend, newsletter integration, state machines, activity stream
  (tracked under Phase 6 as opt-in, project-specific work).

[Unreleased]: https://github.com/bsesic/saas-boilerplate/commits/development
