from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import load_workbook
from rest_framework.test import APIClient

from apps.accounts.tests.factories import UserFactory
from apps.catalog.models import Produit
from apps.finance.models import Depense
from apps.sales.models import Client, Commande, Livraison

pytestmark = pytest.mark.django_db


def test_reports_count_delivery_cost_once_and_exports_all_sheets():
    admin = UserFactory(role="ADMIN", is_staff=True)
    customer = Client.objects.create(nomClient="=HYPERLINK")
    product_a = Produit.objects.create(nomProduit="Produit A", prixVente="10.00", prixAchat="6.00")
    product_b = Produit.objects.create(nomProduit="=FORMULE", prixVente="20.00", prixAchat="12.00")
    order = Commande.objects.create(
        idClient=customer,
        idUser=admin,
        date=date(2026, 1, 10),
        statut=Commande.Statut.CONFIRMEE,
    )
    order.lignes.create(
        idProduit=product_a,
        quantite=2,
        prixUnitaire=Decimal("10.00"),
        coutUnitaire=Decimal("6.00"),
    )
    order.lignes.create(
        idProduit=product_b,
        quantite=1,
        prixUnitaire=Decimal("20.00"),
        coutUnitaire=Decimal("12.00"),
    )
    Livraison.objects.create(
        idCommande=order,
        statut=Livraison.Statut.LIVREE,
        dateLivraison=date(2026, 1, 15),
        cout="3.00",
        fraisFacture="5.00",
    )
    Depense.objects.create(date=date(2026, 1, 16), libelle="Loyer", montant="2.00")

    client = APIClient()
    client.force_login(admin)
    params = {"start_date": "2026-01-01", "end_date": "2026-01-31"}
    summary = client.get("/api/v1/reports/summary/", params)
    assert summary.status_code == 200
    assert summary.data["chiffre_affaires"] == Decimal("45.00")
    assert summary.data["benefice_brut"] == Decimal("18.00")
    assert summary.data["benefice_net"] == Decimal("16.00")

    assert client.get("/api/v1/reports/products/", params).status_code == 200
    assert client.get("/api/v1/reports/orders/", params).data[0]["benefice"] == Decimal("18.00")
    monthly = client.get("/api/v1/reports/monthly/", params)
    assert monthly.status_code == 200
    assert monthly.data[0]["mois"] == date(2026, 1, 1)
    assert monthly.data[0]["benefice_net"] == Decimal("16.00")

    export = client.get("/api/v1/exports/excel/", params)
    assert export.status_code == 200
    assert export["Cache-Control"] == "no-store"
    workbook = load_workbook(filename=BytesIO(export.content))
    assert workbook.sheetnames == ["Résumé", "Produits", "Stock", "Dépenses"]
    assert workbook["Produits"]["A2"].value == "'=FORMULE"


def test_finance_endpoints_are_admin_only_and_date_period_is_validated():
    vendor = UserFactory(role="VENDEUR")
    client = APIClient()
    client.force_login(vendor)
    assert client.get("/api/v1/reports/summary/").status_code == 403
    assert client.get("/api/v1/exports/excel/").status_code == 403

    admin = UserFactory(role="ADMIN", is_staff=True)
    client.force_login(admin)
    invalid = client.get(
        "/api/v1/reports/summary/",
        {"start_date": "2026-02-01", "end_date": "2026-01-01"},
    )
    assert invalid.status_code == 400


def test_pending_orders_dashboard_works_with_commande_reference_column():
    vendor = UserFactory(role="VENDEUR")
    customer = Client.objects.create(nomClient="Client")
    order = Commande.objects.create(idClient=customer, idUser=vendor)

    client = APIClient()
    client.force_login(vendor)
    response = client.get("/api/v1/dashboard/pending-orders/")

    assert response.status_code == 200
    assert response.data == [
        {"public_id": str(order.public_id), "date": order.date, "client": customer.nomClient}
    ]
