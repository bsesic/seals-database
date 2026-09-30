"""Sync published artefacts to the RDF triple store: manage.py sync_rdf

With the default in-memory backend this is a no-op across processes; point
DJANGORDF_BACKEND at Apache Jena Fuseki (via FUSEKI_ENDPOINT) to persist the
catalogue as Linked Open Data and expose it over SPARQL.
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog.rdf_sync import sync_all


class Command(BaseCommand):
    help = "Project all published artefacts onto the RDF triple store."

    def handle(self, *args, **options):
        backend = settings.DJANGORDF_BACKEND.get("class", "?")
        self.stdout.write(f"Backend: {backend}")
        count = sync_all()
        self.stdout.write(self.style.SUCCESS(f"Synced {count} published artefact(s) to RDF."))
