from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from documents.models import Document


@admin.register(Document)
class DocumentAdmin(ModelAdmin, ImportExportModelAdmin, SimpleHistoryAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ("title", "organization", "status", "created_by", "created_at")
    list_filter = ("organization", "status")
    search_fields = ("title", "description")
    autocomplete_fields = ("organization", "created_by")
    # status is a protected FSM field — change it via transitions, not the admin form.
    readonly_fields = ("status",)
