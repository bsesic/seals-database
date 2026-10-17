"""#52 - ObjectType / Material / ScriptType / Language are hierarchical.

Each gained a SKOS ``broader``/``narrower`` self-link (via HierarchicalTerm),
so the typological trees from docs/ontology-from-literature.md can be modelled.
"""

import pytest

from catalog.models import Language, Material, ObjectType, ScriptType

HIERARCHICAL_VOCABS = [ObjectType, Material, ScriptType, Language]


@pytest.mark.parametrize("model", HIERARCHICAL_VOCABS)
def test_broader_narrower_roundtrip(db, model):
    parent = model.objects.create(label=f"{model.__name__} parent")
    child = model.objects.create(label=f"{model.__name__} child", broader=parent)

    assert child.broader == parent
    assert list(parent.narrower.all()) == [child]


@pytest.mark.parametrize("model", HIERARCHICAL_VOCABS)
def test_broader_is_optional(db, model):
    term = model.objects.create(label=f"{model.__name__} root")
    assert term.broader is None


def test_deleting_parent_sets_broader_null(db):
    """on_delete=SET_NULL keeps the child term when its parent is removed."""
    stone = Material.objects.create(label="Stone")
    steatite = Material.objects.create(label="Steatite", broader=stone)

    stone.delete()
    steatite.refresh_from_db()

    assert steatite.broader is None
    assert Material.objects.filter(pk=steatite.pk).exists()
