# Start a new project from the boilerplate

Step-by-step to turn this boilerplate into a fresh SaaS project.

## 1. Clone and rename

```bash
git clone git@github.com:bsesic/saas-boilerplate.git myproject
cd myproject
rm -rf .git && git init        # start a clean history
git remote add origin git@github.com:<you>/myproject.git
```

Decide what to rename: the Django config package stays `core` (no need to rename),
but update user-facing strings — `UNFOLD.SITE_TITLE/SITE_HEADER` and
`SPECTACULAR_SETTINGS.TITLE` in `backend/core/settings.py`, the brand in
`backend/templates/partials/navbar.html` and `footer.html`, and the `frontend`
package name.

## 2. Local environment

```bash
# Infra (Postgres, Redis, Mailpit)
docker compose up -d db redis mailpit

# Backend
cd backend
python -m venv ../venv && source ../venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                 # then edit secrets
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Frontend assets (second terminal) — needs Node 20+
cd frontend
npm install
npm run dev                          # Vite dev server with HMR
```

Visit http://localhost:8000. Mailpit UI: http://localhost:8025. Admin: `/admin/`.
API docs: `/api/docs/`.

## 3. Configure the things you actually use

Everything optional degrades gracefully when unset. Enable per project via `.env`:

- **Social login** — set `<PROVIDER>_CLIENT_ID` + `<PROVIDER>_SECRET` (Google/Microsoft/Apple/Facebook).
- **Billing** — set `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and price ids; otherwise the billing UI shows "not configured".
- **Object storage** — `USE_S3=True` + the `AWS_*` vars for R2/B2/Hetzner/S3.
- **Analytics** — `ANALYTICS_PROVIDER=plausible|matomo` + its settings.
- **Email** — point `EMAIL_*` at your SMTP relay (Brevo/Postmark/SES) for production.

## 4. Build your features on the tenant-scoping foundation

New tenant-scoped models inherit `OrganizationOwnedModel` and views use the
org-scoping mixins:

```python
# models.py
from organizations.models import OrganizationOwnedModel

class Widget(OrganizationOwnedModel):
    name = models.CharField(max_length=200)

# views.py
from organizations.mixins import CurrentOrganizationRequiredMixin, OrgScopedQuerysetMixin

class WidgetListView(CurrentOrganizationRequiredMixin, OrgScopedQuerysetMixin, ListView):
    model = Widget
```

`request.organization` is always set for authenticated users (a personal org is
created on signup). The `documents` app is a complete worked example (uploads,
tags, history, search, API).

## 5. Quality gates (run before every commit)

```bash
cd backend
flake8 .
pytest
```

`pre-commit install` wires these as git hooks. CI runs them on every push to
`main`/`development`.

## 6. Ship

Branch from `development` (`feature/*`, `bugfix/*`), open a PR into `development`,
merge, and cut a release by merging `development` into `main` and tagging it.
See the [deployment runbook](deployment-runbook.md).
