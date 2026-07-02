from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "documents"

    def ready(self):
        from actstream import registry
        from django.contrib.auth import get_user_model

        registry.register(get_user_model())
        Document = self.get_model("Document")
        registry.register(Document)

        # Keep the Elasticsearch index in sync — only when that backend is enabled.
        from documents import search

        if search.elasticsearch_enabled():
            from django.db.models.signals import post_delete, post_save

            def _index(sender, instance, **kwargs):
                search.index_document(instance)

            def _unindex(sender, instance, **kwargs):
                search.delete_document(instance)

            post_save.connect(_index, sender=Document, dispatch_uid="documents.es_index")
            post_delete.connect(_unindex, sender=Document, dispatch_uid="documents.es_unindex")
