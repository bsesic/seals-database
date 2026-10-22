"""#53 - new controlled vocabularies.

SealMorphology (Tufnell head/back/side, hierarchical) plus the flat
EngravingTechnique, MountingDevice, BorderType, BaseLayout, SurfaceTreatment
and Colour vocabularies, each exposed read-only on the public API.
"""

import pytest
from django.urls import reverse

from catalog.models import (
    BaseLayout,
    BorderType,
    Colour,
    EngravingTechnique,
    MountingDevice,
    SealMorphology,
    SurfaceTreatment,
)

FLAT_VOCABS = [
    EngravingTechnique,
    MountingDevice,
    BorderType,
    BaseLayout,
    SurfaceTreatment,
    Colour,
]


@pytest.mark.parametrize("model", FLAT_VOCABS)
def test_flat_vocab_is_creatable_and_flat(db, model):
    term = model.objects.create(label=f"{model.__name__} term")
    assert str(term) == f"{model.__name__} term"
    # Flat vocabularies deliberately have no SKOS broader link.
    assert not hasattr(term, "broader")


def test_seal_morphology_is_hierarchical(db):
    head = SealMorphology.objects.create(label="Head type")
    code = SealMorphology.objects.create(label="A1", broader=head)

    assert code.broader == head
    assert list(head.narrower.all()) == [code]


# --- API: new read-only endpoints are routed and public ---------------------
API_LIST_ROUTES = [
    "v1:sealmorphology-list",
    "v1:engravingtechnique-list",
    "v1:mountingdevice-list",
    "v1:bordertype-list",
    "v1:baselayout-list",
    "v1:surfacetreatment-list",
    "v1:colour-list",
]


@pytest.mark.parametrize("route", API_LIST_ROUTES)
def test_vocab_endpoint_is_public(db, client, route):
    resp = client.get(reverse(route))
    assert resp.status_code == 200


def test_seal_morphology_endpoint_exposes_broader(db, client):
    head = SealMorphology.objects.create(label="Back type")
    SealMorphology.objects.create(label="B2", broader=head)

    rows = client.get(reverse("v1:sealmorphology-list")).json()["results"]
    by_label = {r["label"]: r for r in rows}
    # PKs are UUIDs, serialised as strings in JSON.
    assert str(by_label["B2"]["broader"]) == str(head.pk)


def test_flat_endpoint_has_no_broader_field(db, client):
    Colour.objects.create(label="red-brown")
    rows = client.get(reverse("v1:colour-list")).json()["results"]
    assert rows and "broader" not in rows[0]
