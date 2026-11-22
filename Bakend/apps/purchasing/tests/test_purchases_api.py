from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.catalog.models import Fournisseur, Produit
from apps.inventory.models import Mouvement
from apps.inventory.services import stock_actuel
from apps.purchasing.models import Achat

pytestmark = pytest.mark.django_db


def test_purchase_receives_partial_quantities_and_updates_stock_only_on_receipt():
    admin = UserFactory(role="ADMIN", is_staff=True)
    supplier = Fournisseur.objects.create(nomFournisseur="Grossiste")
    product = Produit.objects.create(nomProduit="Riz", prixVente="100", prixAchat="60")
    client = APIClient()
    client.force_login(admin)

    created = client.post(
        "/api/v1/purchases/",
        {
            "supplier": str(supplier.public_id),
            "items": [{"product": str(product.public_id), "quantity": 10, "unit_price": "60.00"}],
        },
        format="json",
    )
    assert created.status_code == 201
    assert stock_actuel(product) == 0
    purchase_id = created.data["public_id"]

    first = client.post(
        f"/api/v1/purchases/{purchase_id}/receive/",
        {"items": [{"product": str(product.public_id), "quantity": 4}]},
        format="json",
    )
    assert first.status_code == 201
    achat = Achat.objects.get(public_id=purchase_id)
    assert achat.statut == Achat.Statut.PARTIEL
    assert stock_actuel(product) == 4
    assert Mouvement.objects.filter(referenceOperation=first.data["reference"]).count() == 1

    overflow = client.post(
        f"/api/v1/purchases/{purchase_id}/receive/",
        {"items": [{"product": str(product.public_id), "quantity": 7}]},
        format="json",
    )
    assert overflow.status_code == 400
    assert stock_actuel(product) == 4

    final = client.post(
        f"/api/v1/purchases/{purchase_id}/receive/",
        {"items": [{"product": str(product.public_id), "quantity": 6}]},
        format="json",
    )
    assert final.status_code == 201
    achat.refresh_from_db()
    assert achat.statut == Achat.Statut.RECU
    assert stock_actuel(product) == 10


def test_purchase_payments_are_partial_capped_and_admin_only():
    admin = UserFactory(role="ADMIN", is_staff=True)
    vendor = UserFactory(role="VENDEUR")
    supplier = Fournisseur.objects.create(nomFournisseur="Grossiste")
    product = Produit.objects.create(nomProduit="Huile", prixVente="200", prixAchat="80")
    client = APIClient()
    client.force_login(admin)
    created = client.post(
        "/api/v1/purchases/",
        {
            "supplier": str(supplier.public_id),
            "items": [{"product": str(product.public_id), "quantity": 5, "unit_price": "80.00"}],
        },
        format="json",
    )
    purchase_id = created.data["public_id"]

    client.force_login(vendor)
    forbidden = client.post(
        "/api/v1/payments/",
        {"operation": "purchase", "public_id": purchase_id, "montant": "20.00"},
        format="json",
    )
    assert forbidden.status_code == 403

    client.force_login(admin)
    partial = client.post(
        "/api/v1/payments/",
        {"operation": "purchase", "public_id": purchase_id, "montant": "200.00", "mode": "mvola"},
        format="json",
    )
    assert partial.status_code == 201
    assert Decimal(partial.data["montant"]) == Decimal("200.00")

    excessive = client.post(
        "/api/v1/payments/",
        {"operation": "purchase", "public_id": purchase_id, "montant": "201.00"},
        format="json",
    )
    assert excessive.status_code == 400
    detail = client.get(f"/api/v1/purchases/{purchase_id}/")
    assert Decimal(detail.data["solde_restant"]) == Decimal("200.00")
    assert detail.data["statut_paiement"] == "partiellement_paye"
    assert [event["evenement"] for event in detail.data["historique"]] == ["paiement", "creation"]


def test_unreceived_unpaid_purchase_can_be_edited_and_history_keeps_actor():
    admin = UserFactory(role="ADMIN", is_staff=True)
    supplier = Fournisseur.objects.create(nomFournisseur="Grossiste")
    supplier_2 = Fournisseur.objects.create(nomFournisseur="Autre")
    product = Produit.objects.create(nomProduit="Savon", prixVente="100", prixAchat="40")
    client = APIClient()
    client.force_login(admin)
    created = client.post(
        "/api/v1/purchases/",
        {
            "supplier": str(supplier.public_id),
            "items": [{"product": str(product.public_id), "quantity": 2, "unit_price": "40.00"}],
        },
        format="json",
    )
    purchase_id = created.data["public_id"]

    updated = client.patch(
        f"/api/v1/purchases/{purchase_id}/",
        {
            "supplier": str(supplier_2.public_id),
            "items": [{"product": str(product.public_id), "quantity": 3, "unit_price": "45.00"}],
        },
        format="json",
    )
    assert updated.status_code == 200
    assert updated.data["nomFournisseur"] == "Autre"
    assert updated.data["lignes"][0]["quantite"] == 3
    assert [event["evenement"] for event in updated.data["historique"]] == ["modification", "creation"]
    assert all(event["utilisateur"] == admin.email for event in updated.data["historique"])


def test_supplier_return_cannot_exceed_received_quantity_and_reduces_stock():
    admin = UserFactory(role="ADMIN", is_staff=True)
    supplier = Fournisseur.objects.create(nomFournisseur="Grossiste")
    product = Produit.objects.create(nomProduit="Farine", prixVente="100", prixAchat="40")
    client = APIClient()
    client.force_login(admin)
    created = client.post(
        "/api/v1/purchases/",
        {
            "supplier": str(supplier.public_id),
            "items": [{"product": str(product.public_id), "quantity": 10, "unit_price": "40.00"}],
        },
        format="json",
    )
    purchase_id = created.data["public_id"]
    received = client.post(
        f"/api/v1/purchases/{purchase_id}/receive/",
        {"items": [{"product": str(product.public_id), "quantity": 6}]},
        format="json",
    )
    assert received.status_code == 201
    assert stock_actuel(product) == 6

    returned = client.post(
        f"/api/v1/purchases/{purchase_id}/return-to-supplier/",
        {"items": [{"product": str(product.public_id), "quantity": 2}], "motif": "Défectueux"},
        format="json",
    )
    assert returned.status_code == 201
    assert stock_actuel(product) == 4
    assert returned.data["lignes"][0]["quantite_retournee"] == 2
    assert Mouvement.objects.filter(
        typeMouvement=Mouvement.TypeMouvement.RETOUR_FOURNISSEUR,
        referenceOperation=created.data["reference"],
    ).count() == 1

    excessive = client.post(
        f"/api/v1/purchases/{purchase_id}/return-to-supplier/",
        {"items": [{"product": str(product.public_id), "quantity": 5}]},
        format="json",
    )
    assert excessive.status_code == 400
    assert stock_actuel(product) == 4
