"""Sync published artefacts to the RDF triple store: manage.py sync_rdf

With the default in-memory backend this is a no-op across processes; point
DJANGORDF_BACKEND at Apache Jena Fuseki (via FUSEKI_ENDPOINT) to persist the
catalogue as Linked Open Data and expose it over SPARQL.

    manage.py sync_rdf            # sync all published artefacts
    manage.py sync_rdf --prune    # also remove artefacts no longer published
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog.rdf_sync import prune_stale, sync_all


class Command(BaseCommand):
    help = "Project all published artefacts onto the RDF triple store."

    def add_arguments(self, parser):
        parser.add_argument(
            "--prune",
            action="store_true",
            help="Remove RDF artefacts whose source is no longer published.",
        )

    def handle(self, *args, **options):
        backend = settings.DJANGORDF_BACKEND.get("class", "?")
        self.stdout.write(f"Backend: {backend}")
        count = sync_all()
        self.stdout.write(self.style.SUCCESS(f"Synced {count} published artefact(s) to RDF."))
        if options["prune"]:
            removed = prune_stale()
            self.stdout.write(self.style.SUCCESS(f"Pruned {removed} stale artefact(s)."))
