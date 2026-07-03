import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from documents.models import Document
from notifications.models import notify


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def _media(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.mark.django_db
def test_me_requires_auth(api):
    assert api.get(reverse("v1:me")).status_code in (401, 403)


@pytest.mark.django_db
def test_me_get_and_patch(api, make_user):
    user = make_user(username="apiuser")
    api.force_authenticate(user)
    assert api.get(reverse("v1:me")).json()["username"] == "apiuser"
    response = api.patch(reverse("v1:me"), {"first_name": "Api"})
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.first_name == "Api"


@pytest.mark.django_db
def test_documents_api_create_and_scope(api, make_user, _media):
    owner = make_user(username="apidoc")
    api.force_authenticate(owner)
    upload = SimpleUploadedFile("a.txt", b"hello", content_type="text/plain")
    response = api.post(
        reverse("v1:document-list"),
        {"title": "API doc", "file": upload, "tags": ["x", "y"]},
        format="multipart",
    )
    assert response.status_code == 201
    doc = Document.objects.get(title="API doc")
    assert doc.organization == owner.organizations.first()
    assert set(doc.tags.names()) == {"x", "y"}

    # Another user's API list is scoped to their own org.
    other = make_user(username="apiother")
    api.force_authenticate(other)
    listing = api.get(reverse("v1:document-list"))
    assert listing.status_code == 200
    assert listing.json()["count"] == 0


@pytest.mark.django_db
def test_documents_list_is_paginated(api, make_user):
    owner = make_user(username="apipage")
    api.force_authenticate(owner)
    body = api.get(reverse("v1:document-list")).json()
    assert "results" in body and "count" in body


@pytest.mark.django_db
def test_notifications_api_list_and_read(api, make_user):
    user = make_user(username="apinote")
    note = notify(user, "Hello API")
    api.force_authenticate(user)
    assert api.get(reverse("v1:notification-list")).json()["count"] == 1
    response = api.post(reverse("v1:notification-read", args=[note.pk]))
    assert response.status_code == 200
    note.refresh_from_db()
    assert note.unread is False


@pytest.mark.django_db
def test_schema_and_docs(client):
    assert client.get(reverse("schema")).status_code == 200
    assert client.get(reverse("swagger-ui")).status_code == 200
