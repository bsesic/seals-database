"""(Re)build the Elasticsearch index for the catalogue: manage.py reindex_artefacts

No-op unless SEARCH_BACKEND=elasticsearch. Postgres full-text search (the
default) needs no indexing.
"""

from django.core.management.base import BaseCommand

from catalog.search import elasticsearch_enabled, reindex_all


class Command(BaseCommand):
    help = "Index all published artefacts into Elasticsearch."

    def handle(self, *args, **options):
        if not elasticsearch_enabled():
            self.stdout.write(
                "SEARCH_BACKEND is not 'elasticsearch' — nothing to index "
                "(Postgres full-text search needs no index)."
            )
            return
        count = reindex_all()
        self.stdout.write(self.style.SUCCESS(f"Indexed {count} published artefact(s)."))
