"""Stable object IRI resolver (/id/object/<shortid>) with 303 negotiation."""

import pytest
from django.urls import reverse

from catalog.models import Artefact
from core.shortid import encode
from organizations.models import Organization


@pytest.fixture
def artefact(db):
    org = Organization.objects.create(name="Test Org", slug="test-org")
    return Artefact.objects.create(
        organization=org, title="Test Seal", is_published=True
    )


def test_html_request_redirects_to_detail(client, artefact):
    resp = client.get(artefact.get_identity_url())
    assert resp.status_code == 303
    assert resp["Location"] == artefact.get_absolute_url()


def test_rdf_accept_header_redirects_to_rdf(client, artefact):
    resp = client.get(artefact.get_identity_url(), HTTP_ACCEPT="text/turtle")
    assert resp.status_code == 303
    assert resp["Location"] == reverse(
        "catalog:artefact-rdf", kwargs={"slug": artefact.slug}
    )


def test_format_param_preserved_on_redirect(client, artefact):
    resp = client.get(artefact.get_identity_url() + "?format=jsonld")
    assert resp.status_code == 303
    assert resp["Location"].endswith("?format=jsonld")


def test_identity_url_round_trips_through_short_id(artefact):
    assert encode(artefact.pk) == artefact.short_id
    assert artefact.get_identity_url() == reverse(
        "object-identity", kwargs={"shortid": artefact.short_id}
    )


def test_malformed_short_id_returns_404(client):
    # 'u' is not in the Crockford alphabet.
    assert client.get("/id/object/uuuuuu/").status_code == 404


def test_unpublished_artefact_is_not_resolvable(client, db):
    org = Organization.objects.create(name="Org2", slug="org-2")
    draft = Artefact.objects.create(
        organization=org, title="Draft", is_published=False
    )
    assert client.get(draft.get_identity_url()).status_code == 404
