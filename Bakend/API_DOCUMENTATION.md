# Documentation de l'API FlowStock

Cette documentation décrit les routes présentes dans le backend et les formes
de réponses renvoyées par le code actuel.

## Informations générales

- Préfixe des routes métier : `/api/v1/`
- Format des échanges : JSON, sauf l'export Excel.
- Identifiants dans les URL : `public_id` (UUID), pas les clés primaires internes.
- Authentification : session Django (`sessionid`).
- Pour les listes paginées, la taille par défaut est de 20 éléments. La réponse
  contient `count`, `next`, `previous` et `results`.
- Les montants sont renvoyés sous forme de chaînes décimales, par exemple
  `"1250.00"`.
- Les rôles utilisés sont `ADMIN` et `VENDEUR`. Les vendeurs peuvent gérer leurs
  commandes ; les opérations administratives et financières sont réservées aux
  administrateurs. Un superutilisateur Django est également reconnu comme admin.

La documentation interactive OpenAPI est disponible sur `/api/docs/` et le
schéma sur `/api/schema/` quand `ACTIVER_DOCUMENTATION_API=True` (activé par
défaut en développement).

## Authentification et requêtes `curl`

Les routes publiques de connexion et d'inscription créent une session. Garder
les cookies entre requêtes avec `-c` et `-b` :

```bash
curl -i -c cookies.txt \
  -H 'Content-Type: application/json' \
  -d '{"email":"vendeur@example.com","password":"MotDePasse!Long123"}' \
  http://127.0.0.1:8000/api/v1/auth/login/

curl -i -b cookies.txt \
  http://127.0.0.1:8000/api/v1/auth/me/
```

Avec l'authentification par session, les requêtes authentifiées qui modifient
des données doivent également envoyer le jeton CSRF Django dans l'en-tête
`X-CSRFToken`, obtenu depuis le cookie `csrftoken` fourni par l'application.
Ne pas désactiver la protection CSRF pour contourner cette vérification.

## Réponses communes

- `200 OK` : lecture ou modification réussie.
- `201 Created` : ressource créée.
- `204 No Content` : action réussie sans corps de réponse.
- `400 Bad Request` : données manquantes ou invalides.
- `403 Forbidden` : session absente ou droits insuffisants.
- `404 Not Found` : ressource inconnue.
- `409 Conflict` : suppression interdite car la ressource est utilisée ou liée
  à l'historique.

Les erreurs de validation DRF sont généralement renvoyées en JSON, par exemple :

```json
{
  "quantity": ["Assurez-vous que cette valeur est supérieure ou égale à 1."]
}
```

## Comptes et authentification

Toutes les réponses de profil incluent `public_id`, `email`, `nom_complet`,
`role`, `is_active`, `is_staff`, `created_at` et `updated_at`. Le mot de passe
n'est jamais renvoyé.

| Méthode | Route | Accès | Corps de requête | Résultat |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/signup/` | Public | `email`, `nom_complet`, `password` | `201`, profil créé avec le rôle `VENDEUR`, et session ouverte |
| `POST` | `/api/v1/auth/login/` | Public | `email`, `password` | `200`, profil et session ouverte ; `401` si identifiants invalides |
| `POST` | `/api/v1/auth/logout/` | Connecté | Aucun | `204`, session fermée |
| `GET` | `/api/v1/auth/me/` | Connecté | Aucun | `200`, profil courant |
| `PATCH` | `/api/v1/auth/me/` | Connecté | Champs modifiables du profil, notamment `nom_complet` | `200`, profil mis à jour |
| `POST` | `/api/v1/auth/password/change/` | Connecté | `old_password`, `new_password` | `200`, `{"detail":"Mot de passe modifié."}` |
| `POST` | `/api/v1/auth/password/reset/request/` | Public | `email` | `200`, message générique pour ne pas révéler si le compte existe |
| `POST` | `/api/v1/auth/password/reset/confirm/` | Public avec jeton | `uid`, `token`, `new_password` | `200` si le lien est valide ; `400` sinon |

Exemple de création d'un vendeur :

```bash
curl -i -c cookies.txt \
  -H 'Content-Type: application/json' \
  -d '{"email":"vendeur@example.com","nom_complet":"Vendeur Exemple","password":"MotDePasse!Long123"}' \
  http://127.0.0.1:8000/api/v1/auth/signup/
```

Exemple de réponse `201` :

```json
{
  "public_id": "c09b6120-f3f1-48d8-9cc0-658b12446062",
  "email": "vendeur@example.com",
  "nom_complet": "Vendeur Exemple",
  "role": "VENDEUR",
  "is_active": true,
  "is_staff": false,
  "created_at": "2026-11-22T08:00:48.926260Z",
  "updated_at": "2026-11-22T08:00:48.926294Z"
}
```

### Administration des utilisateurs

`{public_id}` est l'UUID public de l'utilisateur.

| Méthode | Route | Accès | Corps de requête | Résultat |
|---|---|---|---|---|
| `GET` | `/api/v1/users/` | Admin | Aucun | Liste paginée des utilisateurs |
| `POST` | `/api/v1/users/` | Admin | `email`, `nom_complet`, `password`, éventuellement `role`, `is_active`, `is_staff` | `201`, utilisateur créé |
| `GET` | `/api/v1/users/{public_id}/` | Admin | Aucun | `200`, détail utilisateur |
| `PATCH` | `/api/v1/users/{public_id}/` | Admin | Champs à modifier | `200`, utilisateur modifié |
| `POST` | `/api/v1/users/{public_id}/deactivate/` | Admin | Aucun | `200`, compte désactivé |

Les méthodes `PUT` et `DELETE` ne sont pas activées pour cette route. Un
administrateur ne peut pas modifier son propre rôle par cette API.

## Catalogue

Les routes de lecture nécessitent une session. Les créations, modifications et
suppression des catégories, fournisseurs et produits nécessitent le rôle admin.
Les produits sont consultables par les vendeurs, mais le champ `prixAchat` leur
est retiré de la réponse.

### Catégories et fournisseurs

| Méthode | Route | Accès | Corps de requête | Résultat |
|---|---|---|---|---|
| `GET` | `/api/v1/categories/` | Connecté | Aucun | Liste paginée : `public_id`, `nomCategorie` |
| `POST` | `/api/v1/categories/` | Admin | `nomCategorie` | `201`, catégorie créée |
| `GET` | `/api/v1/categories/{public_id}/` | Connecté | Aucun | `200`, catégorie |
| `PUT`, `PATCH` | `/api/v1/categories/{public_id}/` | Admin | `nomCategorie` | `200`, catégorie modifiée |
| `DELETE` | `/api/v1/categories/{public_id}/` | Admin | Aucun | `204`; `409` si elle est encore utilisée |
| `GET` | `/api/v1/suppliers/` | Connecté | Aucun | Liste paginée : `public_id`, `nomFournisseur` |
| `POST` | `/api/v1/suppliers/` | Admin | `nomFournisseur` | `201`, fournisseur créé |
| `GET` | `/api/v1/suppliers/{public_id}/` | Connecté | Aucun | `200`, fournisseur |
| `PUT`, `PATCH` | `/api/v1/suppliers/{public_id}/` | Admin | `nomFournisseur` | `200`, fournisseur modifié |
| `DELETE` | `/api/v1/suppliers/{public_id}/` | Admin | Aucun | `204`; `409` si encore utilisé |

### Produits

| Méthode | Route | Accès | Corps / paramètres | Résultat |
|---|---|---|---|---|
| `GET` | `/api/v1/products/` | Connecté | Filtres facultatifs ci-dessous | Liste paginée des produits |
| `POST` | `/api/v1/products/` | Admin | `nomProduit`, `prixVente`, `prixAchat`; facultatifs : `seuilAlerte`, `photo`, `isActif`, `idCategorie`, `idFournisseur` | `201`, produit créé |
| `GET` | `/api/v1/products/{public_id}/` | Connecté | Aucun | `200`, produit |
| `PUT`, `PATCH` | `/api/v1/products/{public_id}/` | Admin | Champs du produit | `200`, produit modifié |
| `DELETE` | `/api/v1/products/{public_id}/` | Admin | Aucun | `204` si sans historique ; sinon `409`, utiliser la désactivation |
| `POST` | `/api/v1/products/{public_id}/deactivate/` | Admin | Aucun | `200`, produit avec `isActif: false` |
| `GET` | `/api/v1/products/{public_id}/stock/` | Connecté | Aucun | `200`, identité du produit, `stock`, `seuilAlerte` |
| `GET` | `/api/v1/products/{public_id}/movements/` | Connecté | Aucun | Liste paginée des mouvements du produit |
| `GET` | `/api/v1/products/low-stock/` | Connecté | Filtres produits facultatifs | Liste paginée des produits actifs au seuil ou sous le seuil |

Filtres acceptés sur `/products/` et `/products/low-stock/` :

- `search` : recherche insensible à la casse dans `nomProduit`.
- `category` : UUID public de la catégorie.
- `supplier` : UUID public du fournisseur.
- `active` : `true` ou `false`.
- `ordering` : `nomProduit`, `-nomProduit`, `prixVente`, `-prixVente`,
  `seuilAlerte` ou `-seuilAlerte`.

Exemple de réponse produit (vue admin) :

```json
{
  "public_id": "34ae9a6f-4fa2-4722-a121-e819e674714b",
  "nomProduit": "Riz 5 kg",
  "prixVente": "12000.00",
  "prixAchat": "9500.00",
  "seuilAlerte": 5,
  "photo": "",
  "isActif": true,
  "idCategorie": "794ba8c7-f763-4c8c-82db-7f97d4150e69",
  "idFournisseur": null
}
```

## Stock et mouvements

La consultation du stock est disponible aux utilisateurs connectés. Seuls les
admins peuvent enregistrer une entrée ou une perte. L'historique est en lecture
seule : les mouvements ne peuvent ni être modifiés ni supprimés.

| Méthode | Route | Accès | Corps de requête | Résultat |
|---|---|---|---|---|
| `GET` | `/api/v1/stock/` | Connecté | Aucun | Liste des produits actifs et de leur stock courant |
| `GET` | `/api/v1/stock/alerts/` | Connecté | Aucun | Liste des produits actifs dont le stock est inférieur ou égal au seuil |
| `POST` | `/api/v1/movements/entries/` | Admin | `product` (UUID produit), `quantity` (entier positif) | `201`, mouvement de type `entree` |
| `POST` | `/api/v1/movements/losses/` | Admin | `product` (UUID produit), `quantity` (entier positif) | `201`, mouvement de type `perte` |
| `GET` | `/api/v1/movements/` | Connecté | Aucun | Liste paginée de l'historique |
| `GET` | `/api/v1/movements/{public_id}/` | Connecté | Aucun | `200`, mouvement |

Exemple de réponse de stock :

```json
[
  {
    "public_id": "34ae9a6f-4fa2-4722-a121-e819e674714b",
    "nomProduit": "Riz 5 kg",
    "stock": 12,
    "seuilAlerte": 5
  }
]
```

Exemple de réponse mouvement :

```json
{
  "public_id": "b634dd84-35ad-4fe9-9b50-799f4a8f996a",
  "produit": "34ae9a6f-4fa2-4722-a121-e819e674714b",
  "typeMouvement": "entree",
  "quantite": 20,
  "date": "2026-11-22"
}
```

Les mouvements créés depuis une réception d'achat ont `referenceOperation` égal
à la référence de réception, ainsi qu'un motif lisible. Les types de mouvement
incluent également les retours clients/fournisseurs et les ajustements positifs
ou négatifs; ceux-ci ne sont pas tous exposés comme actions autonomes dans le
mobile.

## Achats et réceptions

Les achats et paiements fournisseur sont réservés aux administrateurs. Créer un
achat ne change pas le stock. Seules les réceptions validées créent les
mouvements d'entrée. Une réception peut couvrir une partie des quantités
commandées; le serveur refuse tout dépassement et conserve chaque réception.

| Méthode | Route | Accès | Corps | Résultat |
|---|---|---|---|---|
| `GET` | `/api/v1/purchases/` | Admin | Aucun | Liste paginée des achats, lignes, réceptions et paiements |
| `POST` | `/api/v1/purchases/` | Admin | `supplier`, `items` (`product`, `quantity`, `unit_price`); facultatifs `dateCommande`, `lieuAchat`, `modeObtention` | `201`, achat créé sans entrée de stock |
| `GET` | `/api/v1/purchases/{public_id}/` | Admin | Aucun | `200`, achat et soldes |
| `PATCH` | `/api/v1/purchases/{public_id}/` | Admin | Champs facultatifs de création | `200`, modifiable uniquement avant réception et paiement |
| `POST` | `/api/v1/purchases/{public_id}/receive/` | Admin | `items` (`product`, `quantity`); facultatifs `date`, `lieu`, `commentaire` | `201`, réception tracée et stock augmenté |
| `POST` | `/api/v1/purchases/{public_id}/return-to-supplier/` | Admin | `items` (`product`, `quantity`); facultatifs `date`, `motif` | `201`, retour fournisseur tracé et stock diminué sans dépasser le reçu |
| `POST` | `/api/v1/purchases/{public_id}/cancel/` | Admin | Aucun | `200` si aucune réception ni paiement n'existe |
| `GET` | `/api/v1/purchase-receptions/` | Admin | Aucun | Historique paginé des réceptions |

`statut` vaut `en_attente`, `partiellement_recu`, `recu` ou `annule`. Chaque
achat renvoie `reference`, le total, le montant payé, le solde restant, son
statut de paiement (`non_paye`, `partiellement_paye`, `paye`), ses lignes, ses
réceptions et l'historique des actions avec l'utilisateur associé. Les achats réceptionnés ou déjà payés
ne peuvent pas être annulés.

## Paiements

Les paiements sont enregistrés séparément des commandes et des achats. Un
paiement partiel est accepté; le serveur verrouille l'opération pendant le
calcul du solde et refuse tout montant supérieur au reste à payer.

| Méthode | Route | Accès | Corps / paramètres | Résultat |
|---|---|---|---|---|
| `GET` | `/api/v1/payments/?operation=order&public_id={uuid}` | Propriétaire ou admin | Filtre facultatif par opération | Historique des paiements autorisés |
| `POST` | `/api/v1/payments/` | Propriétaire de la commande; achat admin seulement | `operation` (`order` ou `purchase`), `public_id`, `montant`; facultatifs `date`, `mode`, `reference`, `commentaire` | `201`, paiement lié à l'opération |

Les modes acceptés sont `especes`, `mvola`, `orange_money`, `airtel_money`,
`virement` et `autre`. Le solde et les paiements apparaissent dans le détail
d'un achat ou d'une commande.

## Ventes, clients et livraisons

Les vendeurs voient et gèrent uniquement leurs commandes et leurs livraisons ;
les admins peuvent consulter celles de tous les utilisateurs. Les commandes et
livraisons n'exposent pas de route `DELETE`.

### Clients

| Méthode | Route | Accès | Corps / paramètres | Résultat |
|---|---|---|---|---|
| `GET` | `/api/v1/clients/` | Connecté | `search` facultatif | Liste paginée ; recherche par `nomClient` |
| `POST` | `/api/v1/clients/` | Connecté | `nomClient`, `contact`, `adresse` | `201`, client créé |
| `GET` | `/api/v1/clients/{public_id}/` | Connecté | Aucun | `200`, client |
| `PUT`, `PATCH` | `/api/v1/clients/{public_id}/` | Connecté | Champs du client | `200`, client modifié |
| `DELETE` | `/api/v1/clients/{public_id}/` | Admin | Aucun | `204` si sans commande ; sinon `409` |

### Commandes

| Méthode | Route | Accès | Corps de requête | Résultat |
|---|---|---|---|---|
| `GET` | `/api/v1/orders/` | Connecté | Aucun | Liste paginée des commandes autorisées |
| `POST` | `/api/v1/orders/` | Connecté | `client` UUID, `items`: tableau de `{product, quantity}`; facultatifs `remise`, `fraisLivraison` | `201`, commande créée en `en_attente` |
| `GET` | `/api/v1/orders/{public_id}/` | Propriétaire ou admin | Aucun | `200`, commande et lignes |
| `PATCH` | `/api/v1/orders/{public_id}/` | Propriétaire ou admin | Facultatifs : `client`, `items`, `remise`, `fraisLivraison` | `200`, commande mise à jour si son statut le permet |
| `POST` | `/api/v1/orders/{public_id}/confirm/` | Propriétaire ou admin | Aucun | `200`, commande confirmée |
| `POST` | `/api/v1/orders/{public_id}/cancel/` | Propriétaire ou admin | Aucun | `200`, commande annulée |

Exemple de création :

```json
{
  "client": "1c70ce8f-595d-4362-b3e0-94699c0f335f",
  "items": [
    {
      "product": "34ae9a6f-4fa2-4722-a121-e819e674714b",
      "quantity": 2
    }
  ]
}
```

Une commande reçoit une référence `CMD-…`, contient son total, ses paiements et
le solde restant. Ses statuts sont `en_attente`, `confirmee`, `en_preparation`,
`expediee`, `livree`, `annulee` et `retournee`. Une ligne contient `product`,
`quantite`, `prixUnitaire` et, pour l'admin uniquement, `coutUnitaire`.

### Livraisons

| Méthode | Route | Accès | Corps de requête | Résultat |
|---|---|---|---|---|
| `GET` | `/api/v1/deliveries/` | Propriétaire ou admin | Aucun | Liste paginée des livraisons autorisées |
| `POST` | `/api/v1/deliveries/` | Propriétaire de la commande ou admin | `commande` UUID ; facultatifs : `adresse`, `commentaire`, `cout`, `fraisFacture` | `201`, suivi créé pour une commande confirmée |
| `GET` | `/api/v1/deliveries/{public_id}/` | Propriétaire ou admin | Aucun | `200`, livraison |
| `PATCH` | `/api/v1/deliveries/{public_id}/` | Propriétaire ou admin | Champs modifiables de livraison | `200`, livraison mise à jour |
| `POST` | `/api/v1/deliveries/{public_id}/mark-delivered/` | Propriétaire ou admin | Aucun | `200`, statut `livree` et date renseignée |
| `POST` | `/api/v1/deliveries/{public_id}/mark-failed/` | Propriétaire ou admin | Aucun | `200`, statut `echec` |
| `POST` | `/api/v1/deliveries/{public_id}/mark-preparing/` | Propriétaire ou admin | Aucun | `200`, commande et livraison en préparation |
| `POST` | `/api/v1/deliveries/{public_id}/mark-shipped/` | Propriétaire ou admin | Aucun | `200`, commande expédiée et date d'expédition renseignée |
| `POST` | `/api/v1/deliveries/{public_id}/retry/` | Propriétaire ou admin | Aucun | `200`, livraison en échec relancée |
| `POST` | `/api/v1/deliveries/{public_id}/mark-returned/` | Propriétaire ou admin | Aucun | `200`, retour tracé comme mouvement de stock |

Les étapes sont `en_cours`, `en_preparation`, `expediee`, `livree`, `echec`,
`retournee` et `annulee`. Les transitions sont contrôlées côté serveur. Un
retour complet ajoute des mouvements de type `retour_client`; une commande
expédiée ne peut pas être annulée comme une commande en attente.

## Dépenses, tableaux de bord et rapports

Les dépenses et rapports financiers sont réservés aux admins. Les deux routes
de tableau de bord opérationnel (`stock-alerts` et `pending-orders`) sont
accessibles à toute personne connectée.

| Méthode | Route | Accès | Corps / paramètres | Résultat |
|---|---|---|---|---|
| `GET` | `/api/v1/expenses/` | Admin | Aucun | Liste paginée des dépenses |
| `POST` | `/api/v1/expenses/` | Admin | `libelle`, `montant`, facultatif `date` | `201`, dépense créée |
| `GET` | `/api/v1/expenses/{public_id}/` | Admin | Aucun | `200`, dépense |
| `PUT`, `PATCH` | `/api/v1/expenses/{public_id}/` | Admin | Champs de dépense | `200`, dépense modifiée |
| `DELETE` | `/api/v1/expenses/{public_id}/` | Admin | Aucun | `204` |
| `GET` | `/api/v1/dashboard/summary/` | Admin | `start_date` et `end_date` facultatifs | Résumé financier, alertes stock, nombre de commandes en attente |
| `GET` | `/api/v1/dashboard/stock-alerts/` | Connecté | Aucun | Liste des produits en alerte |
| `GET` | `/api/v1/dashboard/pending-orders/` | Connecté | Aucun | Liste des commandes en attente (filtrée par utilisateur pour un vendeur) |
| `GET` | `/api/v1/reports/summary/` | Admin | `start_date`, `end_date` requis | Résumé financier de la période |
| `GET` | `/api/v1/reports/products/` | Admin | `start_date`, `end_date` requis | Chiffre d'affaires et bénéfice par produit |
| `GET` | `/api/v1/reports/orders/` | Admin | `start_date`, `end_date` requis | Résumé des commandes livrées |
| `GET` | `/api/v1/reports/monthly/` | Admin | `start_date`, `end_date` requis | Résultats regroupés par mois |
| `GET` | `/api/v1/exports/excel/` | Admin | `start_date`, `end_date` requis | Fichier `rapport_flowstock.xlsx` |

Les dates doivent être au format `YYYY-MM-DD`, dans l'ordre chronologique, sur
une période maximale d'un an. Sans dates, le résumé du tableau de bord utilise
le début du mois courant jusqu'à aujourd'hui.

Exemple : `/api/v1/reports/summary/?start_date=2026-01-01&end_date=2026-01-31`

Exemple de résumé :

```json
{
  "chiffre_affaires": "250000.00",
  "benefice_brut": "65000.00",
  "depenses": "12000.00",
  "benefice_net": "53000.00",
  "commandes_livrees": 18
}
```

Le tableau de bord admin renvoie cette structure :

```json
{
  "resume_financier": {
    "chiffre_affaires": "250000.00",
    "benefice_brut": "65000.00",
    "depenses": "12000.00",
    "benefice_net": "53000.00",
    "commandes_livrees": 18
  },
  "alertes_stock": [],
  "commandes_en_attente": 3
}
```

## Limites de cette documentation

Les valeurs d'exemples (UUID, dates et montants) sont fictives et servent à
illustrer les formats ; elles ne garantissent pas qu'une ressource portant cet
identifiant existe dans la base. Les routes et règles ci-dessus sont tirées du
code actuel ; l'API OpenAPI générée reste la référence pour les détails de
schéma disponibles à l'exécution.
