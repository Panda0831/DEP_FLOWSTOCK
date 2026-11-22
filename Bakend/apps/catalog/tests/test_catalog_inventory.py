import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.catalog.models import Categorie, Fournisseur, Produit

pytestmark = pytest.mark.django_db


def test_catalog_permissions_and_vendor_buy_price_hidden():
    admin = UserFactory(role="ADMIN", is_staff=True)
    vendor = UserFactory(role="VENDEUR")

    client = APIClient()
    client.force_login(admin)
    category = client.post("/api/v1/categories/", {"nomCategorie": "Boissons"}, format="json")
    assert category.status_code == 201

    supplier = client.post(
        "/api/v1/suppliers/", {"nomFournisseur": "Grossiste Local"}, format="json"
    )
    assert supplier.status_code == 201

    category_public = Categorie.objects.get(nomCategorie="Boissons").public_id
    supplier_public = Fournisseur.objects.get(nomFournisseur="Grossiste Local").public_id
    product = client.post(
        "/api/v1/products/",
        {
            "nomProduit": "Eau 1L",
            "prixVente": "500.00",
            "prixAchat": "300.00",
            "seuilAlerte": 5,
            "idCategorie": str(category_public),
            "idFournisseur": str(supplier_public),
        },
        format="json",
    )
    assert product.status_code == 201

    client.force_login(vendor)
    forbidden = client.post("/api/v1/categories/", {"nomCategorie": "Interdit"}, format="json")
    assert forbidden.status_code == 403

    listed = client.get("/api/v1/products/")
    assert listed.status_code == 200
    assert "prixAchat" not in listed.data["results"][0]


def test_stock_entry_and_alert():
    admin = UserFactory(role="ADMIN", is_staff=True)
    vendor = UserFactory(role="VENDEUR")
    produit = Produit.objects.create(
        nomProduit="Riz", prixVente="100", prixAchat="60", seuilAlerte=3
    )

    client = APIClient()
    client.force_login(vendor)
    forbidden = client.post(
        "/api/v1/movements/entries/",
        {"product": str(produit.public_id), "quantity": 10},
        format="json",
    )
    assert forbidden.status_code == 403

    client.force_login(admin)
    entry = client.post(
        "/api/v1/movements/entries/",
        {"product": str(produit.public_id), "quantity": 10},
        format="json",
    )
    assert entry.status_code == 201

    stock = client.get("/api/v1/stock/")
    assert stock.status_code == 200
    item = next(row for row in stock.data if row["public_id"] == str(produit.public_id))
    assert item["stock"] == 10
    detail = client.get(f"/api/v1/products/{produit.public_id}/stock/")
    assert detail.status_code == 200 and detail.data["stock"] == 10
    movements = client.get(f"/api/v1/products/{produit.public_id}/movements/")
    assert movements.status_code == 200
    assert movements.data["count"] == 1


def test_order_confirmation_requires_available_stock():
    vendor = UserFactory(role="VENDEUR")
    from apps.sales.models import Client

    client_model = Client.objects.create(nomClient="Client Test")
    produit = Produit.objects.create(
        nomProduit="Sucre", prixVente="200", prixAchat="120", seuilAlerte=1
    )

    client = APIClient()
    client.force_login(vendor)
    order = client.post(
        "/api/v1/orders/",
        {
            "client": str(client_model.public_id),
            "items": [{"product": str(produit.public_id), "quantity": 2}],
        },
        format="json",
    )
    assert order.status_code == 201

    confirm = client.post(f"/api/v1/orders/{order.data['public_id']}/confirm/", {}, format="json")
    assert confirm.status_code == 400
