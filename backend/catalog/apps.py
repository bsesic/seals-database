from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"
    verbose_name = "Seal Catalog"

    def ready(self):
        # Keep the Elasticsearch index in sync — only when that backend is on.
        from catalog import search

        if not search.elasticsearch_enabled():
            return

        from django.db.models.signals import post_delete, post_save

        Artefact = self.get_model("Artefact")
        Identifier = self.get_model("Identifier")
        Inscription = self.get_model("Inscription")
        Reading = self.get_model("Reading")

        def index_artefact(sender, instance, **kwargs):
            search.index_artefact(instance)

        def unindex_artefact(sender, instance, **kwargs):
            search.delete_artefact(instance)

        def reindex_parent(sender, instance, **kwargs):
            # A child (identifier/inscription/reading) changed — reindex its
            # artefact so the flattened searchable content stays current.
            try:
                if sender is Reading:
                    artefact = instance.inscription.artefact
                else:
                    artefact = instance.artefact
            except Exception:
                return
            if artefact is not None:
                search.index_artefact(artefact)

        post_save.connect(index_artefact, sender=Artefact, dispatch_uid="catalog.es_index")
        post_delete.connect(unindex_artefact, sender=Artefact, dispatch_uid="catalog.es_unindex")
        for child in (Identifier, Inscription, Reading):
            name = child.__name__
            post_save.connect(
                reindex_parent, sender=child, dispatch_uid=f"catalog.es_reindex_{name}"
            )
            post_delete.connect(
                reindex_parent, sender=child, dispatch_uid=f"catalog.es_reindex_del_{name}"
            )
