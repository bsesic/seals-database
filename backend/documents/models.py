from django.conf import settings
from django.db import models
from django.urls import reverse
from django_fsm import FSMField, transition
from simple_history.models import HistoricalRecords
from taggit.managers import TaggableManager

from organizations.models import OrganizationOwnedModel


def document_upload_path(instance, filename):
    return f"documents/org_{instance.organization_id}/{filename}"


class DocumentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class Document(OrganizationOwnedModel):
    """A tenant-scoped uploaded file with tags and full audit history."""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=document_upload_path)
    # State machine (django-fsm-2): change via the transition methods below.
    # (Not `protected` — that blocks refresh_from_db; transitions still enforce valid moves.)
    status = FSMField(default=DocumentStatus.DRAFT, choices=DocumentStatus.choices)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tags = TaggableManager(blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("documents:detail", kwargs={"pk": self.pk})

    @transition(field=status, source=DocumentStatus.DRAFT, target=DocumentStatus.PUBLISHED)
    def publish(self):
        """Make a draft document published."""

    @transition(
        field=status,
        source=[DocumentStatus.DRAFT, DocumentStatus.PUBLISHED],
        target=DocumentStatus.ARCHIVED,
    )
    def archive(self):
        """Archive a draft or published document."""
