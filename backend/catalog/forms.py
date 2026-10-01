"""Front-end forms for authenticated catalogue data entry."""

from crispy_forms.helper import FormHelper
from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from catalog.models import Artefact, MediaItem


class ArtefactForm(forms.ModelForm):
    """Create / edit an artefact and its metadata (organization, created_by and
    the slug/uuid are set by the view, not the form)."""

    class Meta:
        model = Artefact
        fields = (
            "title", "category", "object_type", "findspot", "find_context",
            "region", "repository", "period", "dating_text", "ruler",
            "origin_region", "origin_note", "is_inscribed", "has_iconography",
            "is_published", "condition", "preservation_note",
            "materials", "iconographic_features", "tags", "description", "notes",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
            "preservation_note": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False  # the template wraps form + image formset


class MediaItemForm(forms.ModelForm):
    class Meta:
        model = MediaItem
        fields = (
            "file", "image_url", "kind", "view", "caption",
            "source", "copyright_note", "license",
        )

    def clean(self):
        cleaned = super().clean()
        if self.has_changed() and not cleaned.get("file") and not cleaned.get("image_url"):
            raise forms.ValidationError(_("Provide an image file or an image URL."))
        return cleaned


MediaItemFormSet = inlineformset_factory(
    Artefact, MediaItem, form=MediaItemForm, extra=3, can_delete=True,
)
