"""Import Publications from a BibTeX file: manage.py import_bibtex refs.bib"""

from django.core.management.base import BaseCommand, CommandError

from catalog.bibtex import import_bibtex


class Command(BaseCommand):
    help = "Import/update Publications from a BibTeX (.bib) file."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to a .bib file")

    def handle(self, *args, **options):
        path = options["path"]
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            raise CommandError(f"Could not read {path}: {exc}")

        created, updated, errors = import_bibtex(text)
        self.stdout.write(self.style.SUCCESS(f"Created {created}, updated {updated}."))
        for err in errors:
            self.stderr.write(self.style.WARNING(f"Skipped {err}"))
