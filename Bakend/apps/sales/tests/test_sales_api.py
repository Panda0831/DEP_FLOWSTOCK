from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.catalog.models import Produit
from apps.inventory.models import Mouvement
from apps.inventory.services import stock_actuel
from apps.sales.models import Client, Commande

pytestmark = pytest.mark.django_db


def create_confirmed_order(client, product, user, quantity=2):
    order = Commande.objects.create(idClient=client, idUser=user)
    order.lignes.create(
        idProduit=product,
        quantite=quantity,
        prixUnitaire=product.prixVente,
        coutUnitaire=product.prixAchat,
    )
    return order


def test_order_patch_confirmation_delivery_and_vendor_cost_redaction():
    vendor = UserFactory(role="VENDEUR")
    admin = UserFactory(role="ADMIN", is_staff=True)
    customer = Client.objects.create(nomClient="Client")
    product = Produit.objects.create(
        nomProduit="Café",
        prixVente="10.00",
        prixAchat="6.00",
        seuilAlerte=1,
    )
    Mouvement.objects.create(
        idProduit=product,
        typeMouvement="entree",
        quantite=8,
        idUser=admin,
    )
    client = APIClient()
    client.force_login(vendor)

    created = client.post(
        "/api/v1/orders/",
        {
            "client": str(customer.public_id),
            "items": [{"product": str(product.public_id), "quantity": 2}],
        },
        format="json",
    )
    assert created.status_code == 201
    order_id = created.data["public_id"]
    assert "coutUnitaire" not in created.data["lignes"][0]

    updated = client.patch(
        f"/api/v1/orders/{order_id}/",
        {"items": [{"product": str(product.public_id), "quantity": 3}]},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.data["lignes"][0]["quantite"] == 3

    confirmed = client.post(f"/api/v1/orders/{order_id}/confirm/", {}, format="json")
    assert confirmed.status_code == 200
    assert Mouvement.objects.filter(idCommande__public_id=order_id).count() == 1
    repeated = client.post(f"/api/v1/orders/{order_id}/confirm/", {}, format="json")
    assert repeated.status_code == 400
    assert Mouvement.objects.filter(idCommande__public_id=order_id).count() == 1

    delivery = client.post(
        "/api/v1/deliveries/",
        {
            "commande": order_id,
            "cout": "1.00",
            "fraisFacture": "2.00",
        },
        format="json",
    )
    assert delivery.status_code == 201
    marked = client.post(
        f"/api/v1/deliveries/{delivery.data['public_id']}/mark-delivered/",
        {},
        format="json",
    )
    assert marked.status_code == 200
    assert marked.data["dateLivraison"] is not None


def test_admin_can_access_all_orders_but_vendor_only_own_orders():
    vendor = UserFactory(role="VENDEUR")
    another_vendor = UserFactory(role="VENDEUR")
    admin = UserFactory(role="ADMIN", is_staff=True)
    customer = Client.objects.create(nomClient="Client")
    product = Produit.objects.create(
        nomProduit="Thé",
        prixVente="5.00",
        prixAchat="2.00",
    )
    create_confirmed_order(customer, product, another_vendor)

    client = APIClient()
    client.force_login(vendor)
    assert client.get("/api/v1/orders/").data["count"] == 0

    client.force_login(admin)
    assert client.get("/api/v1/orders/").data["count"] == 1


def test_client_with_order_cannot_be_deleted():
    admin = UserFactory(role="ADMIN", is_staff=True)
    customer = Client.objects.create(nomClient="Historique")
    product = Produit.objects.create(
        nomProduit="Farine",
        prixVente="8.00",
        prixAchat="4.00",
    )
    create_confirmed_order(customer, product, admin)

    client = APIClient()
    client.force_login(admin)
    response = client.delete(f"/api/v1/clients/{customer.public_id}/")
    assert response.status_code == 409
    assert Client.objects.filter(pk=customer.pk).exists()


def test_order_payment_delivery_transitions_and_return_stock_movement():
    vendor = UserFactory(role="VENDEUR")
    admin = UserFactory(role="ADMIN", is_staff=True)
    customer = Client.objects.create(nomClient="Client", adresse="Antananarivo")
    product = Produit.objects.create(nomProduit="Café", prixVente="500", prixAchat="300")
    Mouvement.objects.create(
        idProduit=product,
        typeMouvement=Mouvement.TypeMouvement.ENTREE,
        quantite=10,
        idUser=admin,
    )
    client = APIClient()
    client.force_login(vendor)
    created = client.post(
        "/api/v1/orders/",
        {
            "client": str(customer.public_id),
            "items": [{"product": str(product.public_id), "quantity": 2}],
            "remise": "100.00",
            "fraisLivraison": "50.00",
        },
        format="json",
    )
    assert created.status_code == 201
    order_id = created.data["public_id"]
    assert Decimal(created.data["montant_total"]) == Decimal("950.00")

    confirmed = client.post(f"/api/v1/orders/{order_id}/confirm/", {}, format="json")
    assert confirmed.status_code == 200
    assert stock_actuel(product) == 8

    payment = client.post(
        "/api/v1/payments/",
        {"operation": "order", "public_id": order_id, "montant": "300.00", "mode": "mvola"},
        format="json",
    )
    assert payment.status_code == 201
    too_much = client.post(
        "/api/v1/payments/",
        {"operation": "order", "public_id": order_id, "montant": "651.00"},
        format="json",
    )
    assert too_much.status_code == 400

    delivery = client.post("/api/v1/deliveries/", {"commande": order_id}, format="json")
    assert delivery.status_code == 201
    delivery_id = delivery.data["public_id"]
    assert delivery.data["adresse"] == "Antananarivo"
    preparing = client.post(f"/api/v1/deliveries/{delivery_id}/mark-preparing/", {}, format="json")
    assert preparing.status_code == 200
    shipped = client.post(f"/api/v1/deliveries/{delivery_id}/mark-shipped/", {}, format="json")
    assert shipped.status_code == 200
    assert shipped.data["dateExpedition"] is not None
    delivered = client.post(f"/api/v1/deliveries/{delivery_id}/mark-delivered/", {}, format="json")
    assert delivered.status_code == 200

    cancelled = client.post(f"/api/v1/orders/{order_id}/cancel/", {}, format="json")
    assert cancelled.status_code == 400
    returned = client.post(f"/api/v1/deliveries/{delivery_id}/mark-returned/", {}, format="json")
    assert returned.status_code == 200
    assert returned.data["statut"] == "retournee"
    assert stock_actuel(product) == 10
    assert Mouvement.objects.filter(typeMouvement=Mouvement.TypeMouvement.RETOUR_CLIENT).count() == 1
    refund = client.post(
        "/api/v1/payments/",
        {
            "operation": "order",
            "public_id": order_id,
            "typePaiement": "remboursement",
            "montant": "200.00",
        },
        format="json",
    )
    assert refund.status_code == 201
    detail = client.get(f"/api/v1/orders/{order_id}/")
    assert Decimal(detail.data["montant_paye"]) == Decimal("100.00")


def test_failed_delivery_can_be_retried():
    vendor = UserFactory(role="VENDEUR")
    admin = UserFactory(role="ADMIN", is_staff=True)
    customer = Client.objects.create(nomClient="Client")
    product = Produit.objects.create(nomProduit="Thé", prixVente="50", prixAchat="30")
    Mouvement.objects.create(idProduit=product, typeMouvement="entree", quantite=5, idUser=admin)
    client = APIClient()
    client.force_login(vendor)
    order = client.post(
        "/api/v1/orders/",
        {"client": str(customer.public_id), "items": [{"product": str(product.public_id), "quantity": 1}]},
        format="json",
    )
    client.post(f"/api/v1/orders/{order.data['public_id']}/confirm/", {}, format="json")
    delivery = client.post("/api/v1/deliveries/", {"commande": order.data["public_id"]}, format="json")
    failed = client.post(f"/api/v1/deliveries/{delivery.data['public_id']}/mark-failed/", {}, format="json")
    assert failed.status_code == 200
    retried = client.post(f"/api/v1/deliveries/{delivery.data['public_id']}/retry/", {}, format="json")
    assert retried.status_code == 200
    assert retried.data["statut"] == "en_cours"
