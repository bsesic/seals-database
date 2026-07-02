import pytest
from django.core import mail
from django.urls import reverse

from organizations.models import Invitation, Organization, Role


@pytest.mark.django_db
def test_personal_org_created_on_signup(make_user):
    user = make_user(username="zoe")
    assert user.organizations.count() == 1
    assert user.organizations.first().get_role(user) == Role.OWNER


@pytest.mark.django_db
def test_create_organization_makes_owner(client, make_user):
    user = make_user()
    client.force_login(user)
    response = client.post(reverse("organizations:create"), {"name": "Acme Inc"})
    assert response.status_code == 302
    org = Organization.objects.get(name="Acme Inc")
    assert org.get_role(user) == Role.OWNER
    assert client.session["active_organization_id"] == org.pk


@pytest.mark.django_db
def test_detail_visible_to_member_only(client, make_user):
    owner = make_user(username="owner1")
    other = make_user(username="other1")
    org = owner.organizations.first()

    client.force_login(other)
    assert client.get(org.get_absolute_url()).status_code == 404

    client.force_login(owner)
    assert client.get(org.get_absolute_url()).status_code == 200


@pytest.mark.django_db
def test_manager_can_invite_sends_email(client, make_user):
    owner = make_user(username="owner2")
    org = owner.organizations.first()
    client.force_login(owner)
    mail.outbox.clear()
    response = client.post(
        reverse("organizations:invite", args=[org.slug]),
        {"email": "new@example.com", "role": Role.MEMBER.value},
    )
    assert response.status_code == 302
    assert Invitation.objects.filter(organization=org, email="new@example.com").exists()
    assert any("invited" in m.subject.lower() for m in mail.outbox)


@pytest.mark.django_db
def test_member_cannot_invite(client, make_user):
    owner = make_user(username="owner3")
    member = make_user(username="member3")
    org = owner.organizations.first()
    org.add_member(member, role=Role.MEMBER)
    client.force_login(member)
    response = client.post(
        reverse("organizations:invite", args=[org.slug]),
        {"email": "x@example.com", "role": Role.MEMBER.value},
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_accept_invitation_creates_membership(client, make_user):
    owner = make_user(username="owner4")
    invitee = make_user(username="invitee4")
    org = owner.organizations.first()
    invitation = Invitation.objects.create(
        organization=org, email="invitee4@example.com", role=Role.MEMBER
    )
    client.force_login(invitee)
    response = client.post(invitation.get_accept_url())
    assert response.status_code == 302
    assert org.get_role(invitee) == Role.MEMBER
    invitation.refresh_from_db()
    assert invitation.is_accepted


@pytest.mark.django_db
def test_switch_organization_sets_session(client, make_user):
    user = make_user(username="switch1")
    second = Organization.objects.create(name="Second")
    second.add_member(user, role=Role.OWNER)
    client.force_login(user)
    response = client.post(reverse("organizations:switch", args=[second.pk]))
    assert response.status_code == 302
    assert client.session["active_organization_id"] == second.pk


@pytest.mark.django_db
def test_cannot_remove_last_owner(client, make_user):
    owner = make_user(username="owner5")
    org = owner.organizations.first()
    membership = org.memberships.get(user=owner)
    client.force_login(owner)
    response = client.post(reverse("organizations:remove_member", args=[org.slug, membership.pk]))
    assert response.status_code == 302
    assert org.memberships.filter(pk=membership.pk).exists()
