"""Background tasks for the catalogue (Celery)."""

from celery import shared_task

from catalog.rdf_sync import prune_stale, sync_all


@shared_task
def sync_rdf_task(prune=True):
    """Sync published artefacts to the triple store (optionally pruning stale ones).

    Schedule it with Celery beat, e.g. in settings:

        CELERY_BEAT_SCHEDULE = {
            "sync-rdf-nightly": {
                "task": "catalog.tasks.sync_rdf_task",
                "schedule": crontab(hour=3, minute=0),
            },
        }
    """
    synced = sync_all()
    pruned = prune_stale() if prune else 0
    return {"synced": synced, "pruned": pruned}
