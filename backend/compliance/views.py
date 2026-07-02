from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View


class DataExportView(LoginRequiredMixin, View):
    """GDPR: download all data we hold about the current user as JSON."""

    def get(self, request):
        user = request.user
        data = {
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "date_joined": user.date_joined.isoformat(),
            },
            "organizations": [
                {"name": m.organization.name, "role": m.role}
                for m in user.memberships.select_related("organization")
            ],
            "documents": [
                {"title": d.title, "created_at": d.created_at.isoformat()}
                for d in user.documents.all()
            ],
            "notifications": [
                {"verb": n.verb, "created_at": n.created_at.isoformat()}
                for n in user.notifications.all()
            ],
        }
        response = JsonResponse(data, json_dumps_params={"indent": 2})
        response["Content-Disposition"] = 'attachment; filename="my-data.json"'
        return response


class AccountDeleteView(LoginRequiredMixin, View):
    """GDPR: soft-delete now (deactivate), hard-delete later via purge command."""

    template_name = "compliance/account_delete.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        user = request.user
        user.is_active = False
        user.deletion_requested_at = timezone.now()
        user.save(update_fields=["is_active", "deletion_requested_at"])
        logout(request)
        messages.success(
            request, _("Your account has been deactivated and will be permanently deleted.")
        )
        return redirect("pages:home")
