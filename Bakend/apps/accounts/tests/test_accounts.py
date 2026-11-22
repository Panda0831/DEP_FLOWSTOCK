import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from .factories import UserFactory

pytestmark = pytest.mark.django_db


def test_create_user_normalized_and_superuser_admin():
    User = get_user_model()
    user = User.objects.create_user(
        email="  User@Example.COM ", password="Motdepasse!Fort12", nom_complet="Test"
    )
    assert user.email == "user@example.com"
    assert user.role == "VENDEUR"
    admin = User.objects.create_superuser(email="Admin@Example.COM", password="Motdepasse!Fort12")
    assert admin.role == "ADMIN"
    assert admin.is_staff and admin.is_superuser


def test_lowercase_email_unique():
    User = get_user_model()
    User.objects.create_user(email="duplicate@example.com", password="Motdepasse!Fort12")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(email="DUPLICATE@example.com", password="Motdepasse!Fort12")


def test_signup_login_me_logout():
    client = APIClient()
    signup = client.post(
        "/api/v1/auth/signup/",
        {
            "email": "  New.User@Example.COM ",
            "nom_complet": "Nouvel Utilisateur",
            "password": "Motdepasse!Fort12",
            "role": "ADMIN",
        },
        format="json",
    )
    assert signup.status_code == 201
    assert signup.data["email"] == "new.user@example.com"
    assert signup.data["role"] == "VENDEUR"

    client.post("/api/v1/auth/logout/", {}, format="json")
    login = client.post(
        "/api/v1/auth/login/",
        {"email": "new.user@example.com", "password": "Motdepasse!Fort12"},
        format="json",
    )
    assert login.status_code == 200
    assert client.get("/api/v1/auth/me/").status_code == 200
    assert client.post("/api/v1/auth/logout/", {}, format="json").status_code == 204


def test_login_failure_is_identical_and_profile_protected():
    client = APIClient()
    assert (
        client.post(
            "/api/v1/auth/login/",
            {"email": "unknown@example.com", "password": "BadPassword!12"},
            format="json",
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login/",
            {"email": "unknown2@example.com", "password": "BadPassword!12"},
            format="json",
        ).status_code
        == 401
    )
    assert client.get("/api/v1/auth/me/").status_code == 403


def test_password_reset_request_is_anti_enumeration():
    client = APIClient()
    known = client.post(
        "/api/v1/auth/password/reset/request/", {"email": "UserFactory@example.com"}, format="json"
    )
    unknown = client.post(
        "/api/v1/auth/password/reset/request/", {"email": "unknown@example.com"}, format="json"
    )
    assert known.status_code == unknown.status_code == 200
    assert known.data == unknown.data


def test_vendor_cannot_admin_user_and_admin_can_list():
    vendor = UserFactory(role="VENDEUR")
    admin = UserFactory(role="ADMIN", is_staff=True)
    client = APIClient()
    client.force_login(vendor)
    assert client.get("/api/v1/users/").status_code == 403
    client.force_login(admin)
    assert client.get("/api/v1/users/").status_code == 200


def test_django_superuser_keeps_admin_api_permissions():
    superuser = UserFactory(role="VENDEUR", is_staff=True, is_superuser=True)
    client = APIClient()
    client.force_login(superuser)

    response = client.post(
        "/api/v1/categories/",
        {"nomCategorie": "Categorie Superuser"},
        format="json",
    )
    assert response.status_code == 201
