"""Persistence policy: 301 redirect on merge, 410 tombstone on delete."""

import pytest

from catalog.models import Artefact, RetiredIdentifier
from organizations.models import Organization


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Org", slug="org")


def _artefact(org, title, published=True):
    return Artefact.objects.create(
        organization=org, title=title, is_published=published
    )


def test_delete_leaves_a_410_tombstone(client, org):
    a = _artefact(org, "Doomed Seal")
    pk, url = a.pk, a.get_identity_url()
    a.delete()  # Django nulls a.pk after this, so capture it first.
    tomb = RetiredIdentifier.objects.get(object_id=pk)
    assert tomb.status == RetiredIdentifier.DELETED
    assert tomb.former_title == "Doomed Seal"
    resp = client.get(url)
    assert resp.status_code == 410


def test_merge_redirects_301_to_successor(client, org):
    a = _artefact(org, "Duplicate")
    b = _artefact(org, "Canonical")
    pk, a_url = a.pk, a.get_identity_url()
    a.retire_as_merged(into=b, reason="duplicate of Canonical")
    resp = client.get(a_url)
    assert resp.status_code == 301
    assert resp["Location"] == b.get_identity_url()
    assert RetiredIdentifier.objects.get(object_id=pk).status == (
        RetiredIdentifier.MERGED
    )


def test_merge_preserves_format_param(client, org):
    a = _artefact(org, "Dup2")
    b = _artefact(org, "Canon2")
    a_url = a.get_identity_url()
    a.retire_as_merged(into=b)
    resp = client.get(a_url + "?format=jsonld")
    assert resp.status_code == 301
    assert resp["Location"].endswith("?format=jsonld")


def test_merged_then_successor_deleted_falls_back_to_410(client, org):
    a = _artefact(org, "Dup3")
    b = _artefact(org, "Canon3")
    pk, a_url = a.pk, a.get_identity_url()
    a.retire_as_merged(into=b)
    b.delete()  # successor gone -> replaced_by SET_NULL
    tomb = RetiredIdentifier.objects.get(object_id=pk)
    assert tomb.http_status == 410
    assert client.get(a_url).status_code == 410


def test_cannot_merge_into_self(org):
    a = _artefact(org, "Self")
    with pytest.raises(ValueError):
        a.retire_as_merged(into=a)
