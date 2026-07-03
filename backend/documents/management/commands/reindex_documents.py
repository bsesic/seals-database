from django.core.management.base import BaseCommand, CommandError

from documents import search
from documents.models import Document


class Command(BaseCommand):
    help = "Index all documents into Elasticsearch (no-op unless SEARCH_BACKEND=elasticsearch)."

    def handle(self, *args, **options):
        if not search.elasticsearch_enabled():
            raise CommandError("SEARCH_BACKEND is not 'elasticsearch'; nothing to reindex.")
        count = 0
        for document in Document.objects.all().iterator():
            search.index_document(document)
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Indexed {count} document(s)."))
