from django.utils.translation import gettext as _

from organizations.models import Organization, Role


def create_personal_organization(sender, instance, created, raw=False, **kwargs):
    """Give every new user a personal organization so tenant scoping always works.

    Projects that don't want this can disconnect the signal in their AppConfig.
    """
    if raw or not created:
        return
    if instance.organizations.exists():
        return
    label = instance.get_username() or instance.email or "personal"
    org = Organization.objects.create(name=_("%(name)s's organization") % {"name": label})
    org.add_member(instance, role=Role.OWNER)
