from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "organizations"

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save

        from organizations.signals import create_personal_organization

        post_save.connect(
            create_personal_organization,
            sender=get_user_model(),
            dispatch_uid="organizations.create_personal_organization",
        )
