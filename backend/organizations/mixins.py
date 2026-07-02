from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from organizations.models import MANAGER_ROLES


class CurrentOrganizationRequiredMixin(LoginRequiredMixin):
    """Require an authenticated user who has an active organization."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and getattr(request, "organization", None) is None:
            messages.info(request, _("Create an organization to continue."))
            return redirect("organizations:create")
        return super().dispatch(request, *args, **kwargs)


class OrgScopedQuerysetMixin:
    """Scope a generic view's queryset and new objects to the current organization.

    Use on views whose model inherits ``OrganizationOwnedModel`` (or has an
    ``organization`` FK). Combine with CurrentOrganizationRequiredMixin.
    """

    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)


class OrganizationManagerRequiredMixin:
    """Require the current user to be owner/admin of the active organization."""

    def dispatch(self, request, *args, **kwargs):
        org = getattr(request, "organization", None)
        if org is None or org.get_role(request.user) not in MANAGER_ROLES:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
