import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from documents.models import Document, DocumentStatus


@pytest.fixture
def _media(tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.mark.django_db
def test_create_document_is_org_scoped(client, make_user, _media):
    owner = make_user(username="downer")
    org = owner.organizations.first()
    client.force_login(owner)
    upload = SimpleUploadedFile("a.txt", b"hello", content_type="text/plain")
    response = client.post(
        reverse("documents:create"),
        {"title": "Report", "description": "Quarterly", "tags": "finance,q1", "file": upload},
    )
    assert response.status_code == 302
    doc = Document.objects.get(title="Report")
    assert doc.organization == org
    assert doc.created_by == owner
    assert set(doc.tags.names()) == {"finance", "q1"}


@pytest.mark.django_db
def test_documents_isolated_between_orgs(client, make_user, _media):
    owner_a = make_user(username="da")
    owner_b = make_user(username="db")
    doc = Document.objects.create(
        organization=owner_a.organizations.first(), title="Secret", created_by=owner_a
    )

    client.force_login(owner_b)
    assert client.get(reverse("documents:list")).status_code == 200
    assert b"Secret" not in client.get(reverse("documents:list")).content
    assert client.get(reverse("documents:detail", args=[doc.pk])).status_code == 404

    client.force_login(owner_a)
    assert client.get(reverse("documents:detail", args=[doc.pk])).status_code == 200


@pytest.mark.django_db
def test_document_search(client, make_user, _media):
    owner = make_user(username="ds")
    org = owner.organizations.first()
    Document.objects.create(organization=org, title="Alpha report", created_by=owner)
    Document.objects.create(organization=org, title="Beta memo", created_by=owner)
    client.force_login(owner)
    response = client.get(reverse("documents:list"), {"q": "alpha"})
    assert b"Alpha report" in response.content
    assert b"Beta memo" not in response.content


@pytest.mark.django_db
def test_documents_require_login(client):
    assert client.get(reverse("documents:list")).status_code == 302


@pytest.mark.django_db
def test_search_database_dispatch(make_user, settings):
    from documents import search

    settings.SEARCH_BACKEND = "database"
    owner = make_user(username="dbsearch")
    org = owner.organizations.first()
    Document.objects.create(organization=org, title="Alpha", created_by=owner)
    Document.objects.create(organization=org, title="Beta", created_by=owner)
    results = search.search_documents(Document.objects.filter(organization=org), "alpha", org)
    assert results.count() == 1


@pytest.mark.django_db
def test_search_elasticsearch_dispatch(make_user, monkeypatch, settings):
    from documents import search

    settings.SEARCH_BACKEND = "elasticsearch"
    owner = make_user(username="essearch")
    org = owner.organizations.first()
    hit = Document.objects.create(organization=org, title="Findable", created_by=owner)
    Document.objects.create(organization=org, title="Other", created_by=owner)
    # Mock the Elasticsearch call so the test needs no ES server.
    monkeypatch.setattr(search, "_es_search_ids", lambda organization, query: [hit.pk])
    results = search.search_documents(Document.objects.filter(organization=org), "x", org)
    assert list(results) == [hit]


@pytest.mark.django_db
def test_document_fsm_transitions(client, make_user):
    owner = make_user(username="fsmowner")
    doc = Document.objects.create(
        organization=owner.organizations.first(), title="Doc", created_by=owner
    )
    assert doc.status == DocumentStatus.DRAFT
    client.force_login(owner)

    response = client.post(reverse("documents:transition", args=[doc.pk, "publish"]))
    assert response.status_code == 302
    doc.refresh_from_db()
    assert doc.status == DocumentStatus.PUBLISHED

    client.post(reverse("documents:transition", args=[doc.pk, "archive"]))
    doc.refresh_from_db()
    assert doc.status == DocumentStatus.ARCHIVED


@pytest.mark.django_db
def test_activity_feed_renders(client, make_user):
    owner = make_user(username="actowner")
    doc = Document.objects.create(
        organization=owner.organizations.first(), title="Doc", created_by=owner
    )
    client.force_login(owner)
    client.post(reverse("documents:transition", args=[doc.pk, "publish"]))
    response = client.get(reverse("documents:activity"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_unfold_admin_document_changelist_loads(client, make_user):
    boss = make_user(username="boss")
    boss.is_staff = True
    boss.is_superuser = True
    boss.save(update_fields=["is_staff", "is_superuser"])
    client.force_login(boss)
    assert client.get("/admin/").status_code == 200
    assert client.get(reverse("admin:documents_document_changelist")).status_code == 200
