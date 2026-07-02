# Deployment runbook

Operational procedures for running this app on benni's server. Reference config lives
in [`../deploy/README.md`](../deploy/README.md); this is the step-by-step.

Releases are cut by merging `development` → `main` and tagging (`vX.Y.Z`). The server
deploys the **current release** (latest tag) from `main`.

## First-time server setup (per project)

1. Create the `saas` system user and `/var/log/saas` (owned by `saas`).
2. Clone into `/opt/saas-boilerplate`; create `/opt/saas-boilerplate/venv` (Python 3.11+).
3. `cp deploy/.env.production.example backend/.env` and fill in real values
   (`DJANGO_DEBUG=False`, `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL`,
   email relay, Stripe, social, `SENTRY_DSN`).
4. Provision the shared services: one Postgres (a DB + user per project) and one Redis.
5. Install systemd units from `deploy/systemd/` into `/etc/systemd/system/`:
   `saas-gunicorn` (or `saas-daphne`), and if used `saas-celery`, `saas-celerybeat`,
   `saas-flower`. `daemon-reload`, `enable --now`.
6. Install the NGINX site from `deploy/nginx/saas-boilerplate.conf`, adjust domain/paths,
   symlink into `sites-enabled`, obtain TLS via certbot, reload NGINX.
7. Ensure Node 20+ is available (for the frontend build in `deploy.sh`).
8. Install log rotation: `deploy/logrotate/saas-boilerplate` → `/etc/logrotate.d/saas-boilerplate`
   (rotates `/var/log/saas/*.log` daily, keeps 14 compressed, `copytruncate`).

## Routine deploy

```bash
sudo -u saas /opt/saas-boilerplate/deploy/deploy.sh
```

`deploy.sh` fetches the release, installs deps, builds frontend assets, runs
`check --deploy`, migrates, collects static, restarts services, and verifies `/readyz`.
It exits non-zero (and you should roll back) if the health check fails.

## Rollback

```bash
# Deploy a specific previous tag instead of the latest
DEPLOY_REF=v1.2.2 sudo -u saas /opt/saas-boilerplate/deploy/deploy.sh
```

Because migrations are written backward-compatible (two-phase: add → deploy → use →
drop), rolling the code back to the previous tag is safe without reversing migrations.
If a migration must be undone, do it deliberately with `migrate <app> <previous>`.

## Zero-downtime notes

- Write backward-compatible migrations; never drop/rename a column in the same release
  that stops using it.
- Gunicorn restarts gracefully (`--graceful-timeout 30`); NGINX keepalive masks the blip.

## Health checks

- `/healthz` — process is up (liveness).
- `/readyz` — database reachable (readiness); used by `deploy.sh`.

## Background jobs

`saas-celery` (worker) + `saas-celerybeat` (scheduler) consume Redis. Monitor with
`saas-flower` (localhost:5555, basic-auth) proxied behind NGINX+TLS.

## Backups

Install `deploy/scripts/backup.sh` as `/usr/local/bin/saas-backup.sh` and enable the
`saas-backup.timer` (daily 02:15). It writes a DB dump (`pg_dump` custom format), a media
tarball, and the gpg-encrypted `.env` to `/var/backups/saas/<timestamp>/`, prunes after
`RETENTION_DAYS`, and pushes offsite via **restic** when `RESTIC_REPOSITORY` is set
(B2/S3). For .env encryption, put a passphrase in `/etc/saas/backup.passphrase`.

**Restore** (quick-reference, also in the script header):

```bash
TS=20260101-021500   # the snapshot to restore
pg_restore -h <host> -U <user> -d <db> -j 4 -c /var/backups/saas/$TS/db.dump
tar -xzf /var/backups/saas/$TS/media.tar.gz -C /opt/saas-boilerplate/backend/
gpg --decrypt --passphrase-file /etc/saas/backup.passphrase \
    /var/backups/saas/$TS/env.gpg > /opt/saas-boilerplate/backend/.env
```

**Test restores** periodically: restore the latest dump into a scratch database and run
`manage.py check`.

## Multiple projects on one server

Run one shared Postgres + Redis; give each project its own `/opt/<project>`, `.env`,
systemd units, and NGINX site. A database and Redis DB number per project.
