from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.core.management.base import CommandError
from django.db import connections, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Categorie, Fournisseur, Produit
from apps.finance.models import Depense, Paiement
from apps.finance.services import calculer_resume, enregistrer_paiement
from apps.inventory.models import Mouvement
from apps.inventory.services import stock_actuel
from apps.purchasing.models import Achat
from apps.purchasing.services import creer_achat, recevoir_achat
from apps.sales.models import Client, Commande, LigneCommande, Livraison


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


class Command(BaseCommand):
    help = "Remplace la base SQLite locale par des données fictives de démonstration."

    def add_arguments(self, parser):
        parser.add_argument("--database", default="default")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Confirme la suppression des données présentes dans db.sqlite3.",
        )

    def handle(self, *args, **options):
        if not options["reset"]:
            raise CommandError("Ajoutez --reset pour confirmer le remplacement de la base locale.")

        alias = options["database"]
        connection = connections[alias]
        database_path = Path(connection.settings_dict["NAME"]).resolve()
        expected_path = (Path(settings.BASE_DIR) / "db.sqlite3").resolve()
        if alias != "default" or connection.vendor != "sqlite" or database_path != expected_path:
            raise CommandError(
                "Réinitialisation bloquée : cette commande ne cible que Bakend/db.sqlite3 "
                "avec la base SQLite par défaut."
            )
        if not database_path.is_file():
            raise CommandError(f"Base locale introuvable : {database_path}")

        call_command("flush", interactive=False, database=alias, verbosity=0)
        with transaction.atomic(using=alias):
            self.seed()

    def seed(self):
        today = timezone.localdate()
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="FlowStockDemo2026!",
            nom_complet="Noro Andrianina",
        )
        seller = User.objects.create_user(
            email="vendeuse@example.com",
            password="FlowStockDemo2026!",
            nom_complet="Soa Rakoto",
            role=User.Role.VENDEUR,
        )

        categories = {
            name: Categorie.objects.create(nomCategorie=name)
            for name in ("Épicerie", "Boissons", "Hygiène", "Entretien", "Papeterie")
        }
        suppliers = {
            name: Fournisseur.objects.create(nomFournisseur=name)
            for name in (
                "Grossiste Analamanga",
                "Tana Distribution",
                "Mada Négoce",
                "Fournitures Atsimondrano",
            )
        }

        specs = [
            ("riz", "Riz local 1 kg", 3500, 4800, 20, "Épicerie", "Grossiste Analamanga", 200),
            ("huile", "Huile de tournesol 1 L", 6500, 8500, 12, "Épicerie", "Mada Négoce", 120),
            ("sucre", "Sucre roux 1 kg", 2800, 4000, 12, "Épicerie", "Grossiste Analamanga", 80),
            ("cafe", "Café moulu 250 g", 7500, 11000, 50, "Épicerie", "Tana Distribution", 35),
            ("lait", "Lait UHT 1 L", 4200, 5800, 12, "Boissons", "Tana Distribution", 60),
            ("eau", "Eau minérale 1,5 L", 900, 1500, 25, "Boissons", "Mada Négoce", 60),
            ("savon", "Savon de toilette", 2100, 3500, 10, "Hygiène", "Mada Négoce", 40),
            ("lessive", "Lessive 1 kg", 5000, 7000, 10, "Entretien", "Tana Distribution", 30),
            ("cahier", "Cahier 96 pages", 1500, 2500, 12, "Papeterie", "Fournitures Atsimondrano", 45),
            ("stylo", "Stylo bille bleu", 700, 1200, 20, "Papeterie", "Fournitures Atsimondrano", 60),
        ]
        products = {}
        for key, name, cost, price, threshold, category, supplier, _opening in specs:
            products[key] = Produit.objects.create(
                nomProduit=name,
                prixAchat=money(cost),
                prixVente=money(price),
                seuilAlerte=threshold,
                idCategorie=categories[category],
                idFournisseur=suppliers[supplier],
            )

        clients = [
            Client.objects.create(
                nomClient=name,
                contact=f"Client démo {index:02d}",
                adresse=address,
            )
            for index, (name, address) in enumerate(
                (
                    ("Épicerie Tsara", "Analamahitsy, Antananarivo"),
                    ("Mamy R. — particulier", "Ankadifotsy, Antananarivo"),
                    ("Marché Soa", "Anosibe, Antananarivo"),
                    ("Bureau Kanto", "Ivandry, Antananarivo"),
                    ("Hery Ando", "Ambohijatovo, Antananarivo"),
                    ("Épicerie Fitiavana", "Ambohidratrimo"),
                    ("Café Tanana", "Isoraka, Antananarivo"),
                    ("Miora R. — particulier", "Ankadimbahoaka, Antananarivo"),
                    ("Cantine Soa", "Ankorondrano, Antananarivo"),
                    ("Boutique Hasina", "Tanjombato, Antananarivo"),
                ),
                start=1,
            )
        ]

        # Opening counts and later receipts form the ledger used by the stock screens.
        opening_by_key = {key: opening for key, *_rest, opening in specs}
        for key, product in products.items():
            Mouvement.objects.create(
                idProduit=product,
                typeMouvement=Mouvement.TypeMouvement.ENTREE,
                quantite=opening_by_key[key],
                date=today - timedelta(days=120),
                idUser=admin,
                motif="Inventaire initial de démonstration",
                referenceOperation="INIT-DEMO-001",
            )

        self.create_purchases(today, products, suppliers, admin)
        self.create_sales(today, products, clients, seller, admin)
        self.create_expenses(today)
        self.create_losses(today, products, admin)

        start = today.replace(day=1)
        summary = calculer_resume(start, today)
        self.stdout.write(self.style.SUCCESS("Base locale remplacée par des données fictives."))
        self.stdout.write(
            "Comptes : admin@example.com et vendeuse@example.com "
            "(mot de passe : FlowStockDemo2026!)"
        )
        self.stdout.write(
            f"Catalogue : {Produit.objects.count()} produits · "
            f"{Categorie.objects.count()} catégories · {Fournisseur.objects.count()} fournisseurs"
        )
        self.stdout.write(
            f"Activité : {Achat.objects.count()} achats · {Commande.objects.count()} commandes · "
            f"{Livraison.objects.count()} livraisons · {Paiement.objects.count()} paiements · "
            f"{Mouvement.objects.count()} mouvements de stock · {Depense.objects.count()} dépenses"
        )
        self.stdout.write(
            f"Résumé du mois : {summary['commandes_livrees']} livraisons terminées · "
            f"ventes {summary['chiffre_affaires']:,.0f} Ar · "
            f"résultat {summary['benefice_net']:,.0f} Ar"
        )
        alerts = [
            f"{product.nomProduit} ({stock_actuel(product)})"
            for product in Produit.objects.order_by("nomProduit")
            if stock_actuel(product) <= product.seuilAlerte
        ]
        self.stdout.write(f"Alertes de stock : {', '.join(alerts) or 'aucune'}")

    def create_purchases(self, today, products, suppliers, admin):
        purchase_specs = [
            {
                "supplier": "Grossiste Analamanga",
                "days_ago": 35,
                "items": [("riz", 40, 3300), ("huile", 20, 6200), ("sucre", 20, 2650)],
                "received": [("riz", 40), ("huile", 20), ("sucre", 20)],
                "paid_ratio": Decimal("1.00"),
                "mode": Achat.Obtention.COMMANDE,
            },
            {
                "supplier": "Tana Distribution",
                "days_ago": 19,
                "items": [("cafe", 24, 7200), ("lait", 24, 4000), ("eau", 48, 800)],
                "received": [("cafe", 24), ("lait", 24), ("eau", 48)],
                "paid_ratio": Decimal("0.70"),
                "mode": Achat.Obtention.ACHAT_DIRECT,
            },
            {
                "supplier": "Mada Négoce",
                "days_ago": 7,
                "items": [("savon", 24, 1900), ("lessive", 12, 4700)],
                "received": [("savon", 24), ("lessive", 6)],
                "paid_ratio": Decimal("0.00"),
                "mode": Achat.Obtention.COMMANDE,
            },
            {
                "supplier": "Fournitures Atsimondrano",
                "days_ago": 2,
                "items": [("cahier", 30, 1400), ("stylo", 50, 600)],
                "received": [],
                "paid_ratio": Decimal("0.00"),
                "mode": Achat.Obtention.COMMANDE,
            },
        ]
        for spec in purchase_specs:
            ordered_on = today - timedelta(days=spec["days_ago"])
            achat = creer_achat(
                fournisseur_id=suppliers[spec["supplier"]].public_id,
                items=[
                    {"product": products[key].public_id, "quantity": quantity, "unit_price": money(price)}
                    for key, quantity, price in spec["items"]
                ],
                user=admin,
                date_commande=ordered_on,
                lieu="Marché d'Anosibe",
                mode_obtention=spec["mode"],
            )
            if spec["received"]:
                recevoir_achat(
                    achat=achat,
                    items=[
                        {"product": products[key].public_id, "quantity": quantity}
                        for key, quantity in spec["received"]
                    ],
                    user=admin,
                    date=ordered_on + timedelta(days=1),
                    lieu="Magasin FlowStock",
                    commentaire="Réception de démonstration",
                )
            if spec["paid_ratio"]:
                enregistrer_paiement(
                    type_operation="purchase",
                    public_id=achat.public_id,
                    montant=(achat.montant_total * spec["paid_ratio"]).quantize(Decimal("0.01")),
                    date=ordered_on + timedelta(days=2),
                    mode=Paiement.Mode.VIREMENT,
                    reference=f"REG-{achat.reference}",
                    commentaire="Règlement de démonstration",
                    user=admin,
                )

    def create_sales(self, today, products, clients, seller, admin):
        sales = [
            (0, 2, "livree", [("riz", 20), ("huile", 3), ("sucre", 6)], 0, 4000, 2500, 1.00),
            (1, 4, "livree", [("cafe", 4), ("lait", 12), ("eau", 24)], 2000, 5000, 3500, 1.00),
            (2, 7, "livree", [("riz", 15), ("savon", 8), ("lessive", 3)], 0, 4000, 2500, 1.00),
            (3, 10, "livree", [("huile", 6), ("sucre", 10), ("cahier", 8)], 1500, 4000, 3000, 0.75),
            (4, 13, "livree", [("cafe", 6), ("eau", 12), ("stylo", 20)], 0, 3500, 2500, 1.00),
            (5, 18, "livree", [("riz", 25), ("lait", 10), ("savon", 10)], 2500, 5000, 3500, 1.00),
            (6, 35, "livree", [("lessive", 6), ("cahier", 12), ("stylo", 30)], 0, 4000, 3000, 1.00),
            (7, 41, "livree", [("huile", 5), ("sucre", 10), ("eau", 20)], 0, 3500, 2500, 1.00),
            (8, 48, "livree", [("cafe", 5), ("savon", 10), ("lait", 8)], 1000, 4000, 3000, 0.80),
            (9, 58, "livree", [("riz", 30), ("huile", 4), ("cahier", 6)], 0, 5000, 3500, 1.00),
            (2, 26, "livree", [("riz", 12), ("sucre", 5)], 0, 4000, 2500, 1.00),
            (3, 30, "livree", [("cafe", 2), ("lait", 6), ("eau", 12)], 0, 4000, 2500, 1.00),
            (0, 3, "retournee", [("cafe", 2), ("lait", 4)], 0, 3500, 2500, 1.00),
            (6, 1, "confirmee", [("riz", 8), ("huile", 2)], 0, 4000, 3000, 0.50),
            (7, 2, "preparation", [("savon", 6), ("lessive", 2)], 0, 3500, 2500, 0.00),
            (8, 3, "expediee", [("cafe", 2), ("eau", 12)], 0, 3500, 2500, 0.70),
            (9, 2, "echec", [("lait", 6), ("eau", 12)], 0, 3500, 2500, 0.30),
            (5, 1, "en_attente", [("riz", 5), ("sucre", 3)], 0, 0, 0, 0.00),
            (2, 4, "annulee", [("huile", 2), ("savon", 3)], 0, 0, 0, 0.00),
        ]
        states = {
            "en_attente": Commande.Statut.EN_ATTENTE,
            "confirmee": Commande.Statut.CONFIRMEE,
            "preparation": Commande.Statut.EN_PREPARATION,
            "expediee": Commande.Statut.EXPEDIEE,
            "livree": Commande.Statut.LIVREE,
            "echec": Commande.Statut.CONFIRMEE,
            # Le versement initial est enregistré avant de passer la commande en retour.
            "retournee": Commande.Statut.LIVREE,
            "annulee": Commande.Statut.ANNULLEE,
        }
        delivery_states = {
            "confirmee": Livraison.Statut.EN_COURS,
            "preparation": Livraison.Statut.EN_PREPARATION,
            "expediee": Livraison.Statut.EXPEDIEE,
            "livree": Livraison.Statut.LIVREE,
            "echec": Livraison.Statut.ECHEC,
            "retournee": Livraison.Statut.LIVREE,
        }
        for index, (client_index, days_ago, state, lines, discount, fee, delivery_cost, paid_ratio) in enumerate(sales):
            sold_on = today - timedelta(days=days_ago)
            user = seller if index % 3 else admin
            commande = Commande.objects.create(
                idClient=clients[client_index],
                idUser=user,
                date=sold_on,
                statut=states[state],
                remise=money(discount),
                fraisLivraison=money(fee),
            )
            for key, quantity in lines:
                product = products[key]
                LigneCommande.objects.create(
                    idCommande=commande,
                    idProduit=product,
                    quantite=quantity,
                    prixUnitaire=product.prixVente,
                    coutUnitaire=product.prixAchat,
                )

            ships_stock = state not in ("en_attente", "annulee")
            if ships_stock:
                for key, quantity in lines:
                    Mouvement.objects.create(
                        idProduit=products[key],
                        typeMouvement=Mouvement.TypeMouvement.SORTIE,
                        quantite=quantity,
                        date=sold_on,
                        idUser=user,
                        idCommande=commande,
                        motif=f"Vente de démonstration {commande.reference}",
                        referenceOperation=commande.reference,
                    )

            if state in delivery_states:
                Livraison.objects.create(
                    idCommande=commande,
                    adresse=clients[client_index].adresse,
                    commentaire="Livraison fictive de démonstration",
                    dateExpedition=sold_on - timedelta(days=1)
                    if state in ("expediee", "livree", "retournee")
                    else None,
                    dateLivraison=sold_on if state in ("livree", "retournee") else None,
                    statut=delivery_states[state],
                    cout=money(delivery_cost),
                    fraisFacture=money(fee),
                )

            if paid_ratio:
                payment_amount = (commande.montant_total * Decimal(str(paid_ratio))).quantize(
                    Decimal("0.01")
                )
                enregistrer_paiement(
                    type_operation="order",
                    public_id=commande.public_id,
                    montant=payment_amount,
                    date=sold_on + timedelta(days=1),
                    mode=(Paiement.Mode.MVOLA if index % 2 else Paiement.Mode.ESPECES),
                    reference=f"ENC-{commande.reference}",
                    commentaire="Paiement fictif de démonstration",
                    user=user,
                )

            if state == "retournee":
                for key, quantity in lines:
                    Mouvement.objects.create(
                        idProduit=products[key],
                        typeMouvement=Mouvement.TypeMouvement.RETOUR_CLIENT,
                        quantite=quantity,
                        date=sold_on + timedelta(days=2),
                        idUser=admin,
                        idCommande=commande,
                        motif=f"Retour fictif {commande.reference}",
                        referenceOperation=commande.reference,
                    )
                commande.statut = Commande.Statut.RETOURNEE
                commande.save(update_fields=("statut",))
                livraison = commande.livraison
                livraison.statut = Livraison.Statut.RETOURNEE
                livraison.save(update_fields=("statut",))
                enregistrer_paiement(
                    type_operation="order",
                    public_id=commande.public_id,
                    montant=payment_amount,
                    type_paiement=Paiement.TypePaiement.REMBOURSEMENT,
                    date=sold_on + timedelta(days=2),
                    mode=Paiement.Mode.MVOLA,
                    reference=f"RBT-{commande.reference}",
                    commentaire="Remboursement fictif de démonstration",
                    user=admin,
                )

    def create_expenses(self, today):
        expenses = [
            (today.replace(day=1), "Loyer du magasin", 80000),
            (today - timedelta(days=12), "Électricité et eau", 26000),
            (today - timedelta(days=9), "Transport des marchandises", 18000),
            (today - timedelta(days=5), "Téléphone et internet", 15000),
            (today - timedelta(days=2), "Sacs et emballages", 12000),
            (today.replace(day=1) - timedelta(days=1), "Loyer du magasin", 80000),
            (today - timedelta(days=35), "Électricité et eau", 24000),
            (today - timedelta(days=39), "Transport des marchandises", 15000),
            (today - timedelta(days=42), "Téléphone et internet", 15000),
        ]
        for date, label, amount in expenses:
            Depense.objects.create(date=date, libelle=label, montant=money(amount))

    def create_losses(self, today, products, admin):
        for key, quantity, days_ago, note in (
            ("eau", 2, 6, "Bouteilles endommagées"),
            ("cahier", 1, 3, "Article abîmé en magasin"),
        ):
            Mouvement.objects.create(
                idProduit=products[key],
                typeMouvement=Mouvement.TypeMouvement.PERTE,
                quantite=quantity,
                date=today - timedelta(days=days_ago),
                idUser=admin,
                motif=note,
                referenceOperation="PERTE-DEMO",
            )
