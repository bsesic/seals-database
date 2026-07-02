from actstream import action as actstream_action
from actstream.models import actor_stream
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from documents.forms import DocumentForm
from documents.models import Document, DocumentStatus
from documents.search import search_documents
from organizations.mixins import CurrentOrganizationRequiredMixin, OrgScopedQuerysetMixin


class DocumentListView(CurrentOrganizationRequiredMixin, OrgScopedQuerysetMixin, ListView):
    model = Document
    template_name = "documents/document_list.html"
    context_object_name = "documents"
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get("q", "")
        return search_documents(qs, query, self.request.organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class DocumentDetailView(CurrentOrganizationRequiredMixin, OrgScopedQuerysetMixin, DetailView):
    model = Document
    template_name = "documents/document_detail.html"
    context_object_name = "document"


class DocumentCreateView(CurrentOrganizationRequiredMixin, OrgScopedQuerysetMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        actstream_action.send(self.request.user, verb="created document", target=self.object)
        return response


class DocumentUpdateView(CurrentOrganizationRequiredMixin, OrgScopedQuerysetMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = "documents/document_form.html"


class DocumentDeleteView(CurrentOrganizationRequiredMixin, OrgScopedQuerysetMixin, DeleteView):
    model = Document
    template_name = "documents/document_confirm_delete.html"
    success_url = reverse_lazy("documents:list")


class DocumentTransitionView(CurrentOrganizationRequiredMixin, View):
    """Run an FSM transition (publish/archive) on a document."""

    def post(self, request, pk, action):
        document = get_object_or_404(
            Document.objects.filter(organization=request.organization), pk=pk
        )
        if action == "publish" and document.status == DocumentStatus.DRAFT:
            document.publish()
            document.save()
            actstream_action.send(request.user, verb="published document", target=document)
            messages.success(request, _("Document published."))
        elif action == "archive" and document.status in (
            DocumentStatus.DRAFT,
            DocumentStatus.PUBLISHED,
        ):
            document.archive()
            document.save()
            actstream_action.send(request.user, verb="archived document", target=document)
            messages.success(request, _("Document archived."))
        else:
            messages.error(request, _("That action is not allowed from the current state."))
        return redirect(document.get_absolute_url())


class ActivityListView(LoginRequiredMixin, ListView):
    """Recent activity performed by the current user (django-activity-stream)."""

    template_name = "documents/activity.html"
    context_object_name = "actions"
    paginate_by = 20

    def get_queryset(self):
        return actor_stream(self.request.user)
