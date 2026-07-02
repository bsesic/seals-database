import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    OWNER = "owner", _("Owner")
    ADMIN = "admin", _("Admin")
    MEMBER = "member", _("Member")


# Roles allowed to manage members and invitations.
MANAGER_ROLES = {Role.OWNER, Role.ADMIN}


def generate_invite_token():
    return secrets.token_urlsafe(32)


class Organization(models.Model):
    """A tenant. Almost everything in the app is scoped to an organization."""

    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Membership",
        related_name="organizations",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.name) or "org"
        slug = base
        i = 2
        while Organization.objects.exclude(pk=self.pk).filter(slug=slug).exists():
            slug = f"{base}-{i}"
            i += 1
        return slug

    def get_absolute_url(self):
        return reverse("organizations:detail", kwargs={"slug": self.slug})

    def add_member(self, user, role=Role.MEMBER):
        membership, _created = Membership.objects.get_or_create(
            organization=self, user=user, defaults={"role": role}
        )
        return membership

    def get_role(self, user):
        if not user or not user.is_authenticated:
            return None
        membership = self.memberships.filter(user=user).first()
        return membership.role if membership else None

    def has_member(self, user):
        return self.get_role(user) is not None

    def can_manage(self, user):
        return self.get_role(user) in MANAGER_ROLES


class Membership(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("organization", "user")
        ordering = ["organization", "user"]

    def __str__(self):
        return f"{self.user} @ {self.organization} ({self.role})"

    @property
    def is_owner(self):
        return self.role == Role.OWNER


class Invitation(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    token = models.CharField(max_length=64, unique=True, default=generate_invite_token)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} -> {self.organization} ({self.role})"

    @property
    def is_accepted(self):
        return self.accepted_at is not None

    def get_accept_url(self):
        return reverse("organizations:accept_invitation", kwargs={"token": self.token})

    def accept(self, user):
        """Turn the invitation into a membership for ``user``."""
        membership = self.organization.add_member(user, role=self.role)
        self.accepted_at = timezone.now()
        self.save(update_fields=["accepted_at"])
        return membership


class OrgQuerySet(models.QuerySet):
    def for_organization(self, organization):
        return self.filter(organization=organization)


class OrganizationOwnedModel(models.Model):
    """Abstract base for any tenant-scoped model.

    Inherit from this and use ``Model.objects.for_organization(org)`` (or the
    OrgScopedQuerysetMixin) to keep data isolated per tenant.
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="+")

    objects = OrgQuerySet.as_manager()

    class Meta:
        abstract = True
