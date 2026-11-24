# Plan des API — Application de gestion de stock

> Feuille de route pour développer, tester et déployer les API de l'application de gestion de stock avec Django et PostgreSQL.

## 1. Objectif

Créer une API interne qui permet à l'interface de l'application de gérer :

- les comptes et les rôles ;
- les catégories, fournisseurs et produits ;
- les entrées, sorties et pertes de stock ;
- les clients, commandes et lignes de commande ;
- les livraisons ;
- les dépenses et les bénéfices ;
- le tableau de bord et les exports Excel.

**Important :** le projet n'a pas besoin d'une API externe payante pour ces fonctions. Les API décrites ici sont les endpoints que nous allons créer dans notre propre application Django.

## 1.1 Répartition de réalisation en six parties

### Partie 1 — Fondations, comptes et conventions
- Finaliser l'environnement DRF, les erreurs, les sessions, les rôles et la réinitialisation.
- Adapter les noms métiers aux tables françaises du schéma fourni.
- Tester les endpoints de connexion, profil et administration des comptes.

### Partie 2 — Catalogue
- Créer les applications Django `Categorie`, `Fournisseur` et `Produit`.
- Implémenter les routes de catégories, fournisseurs, produits et recherche.
- Appliquer les droits admin/vendeur et masquer `prixAchat` aux vendeurs.

### Partie 3 — Stock
- Créer les modèles `Mouvement` et les règles de stock.
- Implémenter les entrées, pertes, alertes et historique.
- Interdire toute modification ou suppression des mouvements.

### Partie 4 — Ventes et livraisons
- Créer `Client`, `Commande`, `LigneCommande` et `Livraison`.
- Implémenter confirmation, annulation, livraisons et verrouillage du stock.
- Utiliser des transactions pour les opérations critiques.

### Partie 5 — Finance et tableau de bord
- Créer `Depense` et les vues de statistiques.
- Calculer chiffre d'affaires, bénéfices et dépenses.
- Restreindre les données financières aux administrateurs.

### Partie 6 — Export, tests et production
- Ajouter l'export Excel et les contrôles de période.
- Tester les permissions, validations, concurrences et opérations métier.
- Préparer PostgreSQL, Docker, HTTPS, sauvegardes et supervision.

## 2. Technologies retenues

| Besoin | Technologie |
|---|---|
| Backend | Python 3.12+ et Django 5.2 |
| API REST | Django REST Framework (DRF) |
| Base de données | PostgreSQL 16 |
| Authentification | Django SessionAuthentication au départ |
| Protection CSRF | Protection Django/DRF |
| Interface | Templates Django, HTML, Bootstrap et HTMX |
| Export Excel | openpyxl |
| Déploiement | Docker Compose et Nginx ou Caddy |

### Authentification : choix simple

L'interface étant prévue dans le même projet Django, commencer avec les sessions Django et la protection CSRF. Cela évite d'ajouter immédiatement une gestion de JWT.

Si une application mobile ou un frontend indépendant est ajouté plus tard, on pourra étudier une authentification par jeton. Ne pas installer plusieurs systèmes d'authentification sans besoin.

## 3. Règles communes à toutes les API

- Préfixe des routes : `/api/v1/`.
- Format des échanges : JSON, sauf les photos et les fichiers exportés.
- Utiliser les codes HTTP correctement : `200`, `201`, `204`, `400`, `401`, `403`, `404` et `409`.
- Vérifier les droits côté serveur pour chaque endpoint.
- Ne jamais faire confiance à un `idUser`, un rôle, un prix ou un montant envoyé par le navigateur sans validation.
- Utiliser des serializers DRF pour valider les données.
- Paginer les listes et permettre la recherche et le filtrage.
- Ne pas exposer le prix d'achat aux vendeurs.
- Ne pas supprimer physiquement les commandes ni les mouvements de stock.
- Utiliser des transactions PostgreSQL pour les opérations qui touchent aux commandes et au stock.
- Utiliser des identifiants publics UUID dans les URLs exposées, conformément à la conception du projet.

Réponse d'erreur conseillée :

```json
{
  "detail": "Le stock disponible est insuffisant.",
  "code": "stock_insuffisant"
}
```

## 4. Matrice des rôles

| Fonction | Admin | Vendeur |
|---|:---:|:---:|
| Se connecter / se déconnecter | Oui | Oui |
| Consulter les produits | Oui | Oui |
| Créer ou modifier un produit | Oui | Non |
| Voir le prix d'achat | Oui | Non |
| Gérer les catégories et fournisseurs | Oui | Consultation |
| Enregistrer une entrée ou une perte | Oui | Non |
| Créer une commande | Oui | Oui |
| Confirmer ou annuler une commande | Oui | Ses propres commandes |
| Consulter les clients | Oui | Oui |
| Gérer les livraisons | Oui | Livraisons de ses propres commandes |
| Gérer les dépenses | Oui | Non |
| Voir les bénéfices et statistiques financières | Oui | Non |
| Exporter les rapports | Oui | Non |
| Gérer les utilisateurs et les rôles | Oui | Non |

Ces règles appliquent le principe du moindre privilège : le vendeur ne gère pas le catalogue ni les mouvements d'inventaire, mais peut traiter ses commandes et livraisons. Un superutilisateur Django conserve les droits administrateur même si son champ `role` est mal renseigné.

## 5. Liste des API à développer

Toutes les routes ci-dessous sont relatives à `/api/v1`.

### 5.1. API Comptes et authentification

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `POST` | `/auth/login/` | Ouvrir une session | Public |
| `POST` | `/auth/logout/` | Fermer la session | Connecté |
| `GET` | `/auth/me/` | Obtenir son profil et son rôle | Connecté |
| `GET` | `/users/` | Lister les utilisateurs | Admin |
| `POST` | `/users/` | Créer un utilisateur | Admin |
| `GET` | `/users/{uuid}/` | Consulter un utilisateur | Admin |
| `PATCH` | `/users/{uuid}/` | Modifier un utilisateur | Admin |
| `POST` | `/users/{uuid}/deactivate/` | Désactiver un compte | Admin |
| `POST` | `/auth/password/change/` | Changer son mot de passe | Connecté |
| `POST` | `/auth/password/reset/request/` | Demander une réinitialisation | Public |
| `POST` | `/auth/password/reset/confirm/` | Confirmer la réinitialisation | Public avec jeton |

Règles :
- Les mots de passe sont traités par le système de hachage Django ; jamais stockés en clair.
- La création du premier administrateur se fait avec `createsuperuser`.
- Un utilisateur ne peut jamais modifier son propre rôle en envoyant une requête.
- Les réponses de connexion et de réinitialisation ne doivent pas révéler si une adresse e-mail existe.
- Limiter les tentatives de connexion et journaliser les événements de sécurité.

### 5.2. API Catégories

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `GET` | `/categories/` | Lister les catégories | Connecté |
| `POST` | `/categories/` | Créer une catégorie | Admin |
| `GET` | `/categories/{id}/` | Consulter une catégorie | Connecté |
| `PATCH` | `/categories/{id}/` | Modifier une catégorie | Admin |
| `DELETE` | `/categories/{id}/` | Supprimer si elle n'est pas utilisée | Admin |

Empêcher la suppression d'une catégorie encore utilisée par un produit. Proposer une désactivation si nécessaire.

### 5.3. API Fournisseurs

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `GET` | `/suppliers/` | Lister les fournisseurs | Connecté |
| `POST` | `/suppliers/` | Ajouter un fournisseur | Admin |
| `GET` | `/suppliers/{id}/` | Consulter un fournisseur | Connecté |
| `PATCH` | `/suppliers/{id}/` | Modifier un fournisseur | Admin |
| `DELETE` | `/suppliers/{id}/` | Supprimer s'il n'est pas utilisé | Admin |

### 5.4. API Produits

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `GET` | `/products/` | Lister les produits | Connecté |
| `POST` | `/products/` | Créer un produit | Admin |
| `GET` | `/products/{uuid}/` | Consulter un produit | Connecté |
| `PATCH` | `/products/{uuid}/` | Modifier un produit | Admin |
| `POST` | `/products/{uuid}/deactivate/` | Désactiver un produit | Admin |
| `GET` | `/products/{uuid}/stock/` | Consulter le stock actuel | Connecté |
| `GET` | `/products/low-stock/` | Lister les produits en alerte | Connecté |
| `GET` | `/products/{uuid}/movements/` | Historique des mouvements du produit | Connecté |

Filtres utiles :
- `?search=nom`
- `?category=ID`
- `?supplier=ID`
- `?active=true`
- `?ordering=nomProduit`

Règles :
- Prix de vente, prix d'achat et seuil d'alerte ne peuvent pas être négatifs.
- Le vendeur ne reçoit jamais `prixAchat` ni `coutUnitaire`.
- Les photos sont envoyées en `multipart/form-data`, contrôlées côté serveur et stockées dans `media/`.
- Un produit utilisé dans l'historique est désactivé plutôt que supprimé.

### 5.5. API Stock et mouvements

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `GET` | `/stock/` | Consulter le stock des produits | Connecté |
| `GET` | `/stock/alerts/` | Consulter les alertes | Connecté |
| `GET` | `/movements/` | Consulter l'historique des mouvements | Connecté |
| `POST` | `/movements/entries/` | Enregistrer une entrée | Autorisé |
| `POST` | `/movements/losses/` | Enregistrer une perte | Autorisé |
| `GET` | `/products/{uuid}/movements/` | Historique d'un produit | Connecté |

Exemple d'entrée :

```json
{
  "product": "UUID_DU_PRODUIT",
  "quantity": 20
}
```

Exemple de perte :

```json
{
  "product": "UUID_DU_PRODUIT",
  "quantity": 2
}
```

Règles essentielles :
- Le stock est calculé à partir des mouvements : entrées moins sorties moins pertes.
- Une sortie liée à une vente est créée par le service de confirmation de commande, pas par un endpoint libre.
- Un mouvement enregistré est immuable : pas de modification ni de suppression.
- Pour corriger une erreur, créer un mouvement inverse.
- Verrouiller le produit avec `select_for_update()` pendant une sortie et refuser si le stock est insuffisant.
- La création du mouvement et la confirmation de commande doivent être dans une même transaction.

### 5.6. API Clients

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `GET` | `/clients/` | Lister et rechercher les clients | Connecté |
| `POST` | `/clients/` | Créer un client | Connecté |
| `GET` | `/clients/{id}/` | Consulter un client | Connecté |
| `PATCH` | `/clients/{id}/` | Modifier un client | Connecté |
| `DELETE` | `/clients/{id}/` | Supprimer si aucune commande ne le référence | Admin |

Limiter l'accès aux coordonnées et adresses des clients aux personnes qui en ont besoin.

### 5.7. API Commandes et lignes de commande

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `GET` | `/orders/` | Lister les commandes autorisées | Connecté |
| `POST` | `/orders/` | Créer une commande et ses lignes | Connecté |
| `GET` | `/orders/{uuid}/` | Consulter une commande | Connecté |
| `PATCH` | `/orders/{uuid}/` | Modifier une commande encore modifiable | Autorisé |
| `POST` | `/orders/{uuid}/confirm/` | Confirmer et retirer le stock | Autorisé |
| `POST` | `/orders/{uuid}/cancel/` | Annuler une commande | Autorisé |

Exemple de création :

```json
{
  "client": 12,
  "items": [
    {
      "product": "UUID_PRODUIT_1",
      "quantity": 2
    },
    {
      "product": "UUID_PRODUIT_2",
      "quantity": 1
    }
  ]
}
```

Règles :
- Le serveur récupère lui-même le prix de vente et le coût d'achat au moment de la création.
- Ces valeurs sont copiées dans les lignes de commande et restent figées.
- Une commande ne peut contenir qu'une ligne par produit ; les quantités doivent être strictement positives.
- La confirmation vérifie le stock puis crée les mouvements de sortie dans une transaction.
- Une confirmation répétée ne doit pas retirer le stock une deuxième fois.
- Une commande annulée ne peut pas être confirmée ensuite.
- Si une commande déjà confirmée est annulée, créer les mouvements inverses nécessaires.
- Ne pas supprimer physiquement une commande.
- Les vendeurs ne voient que les commandes auxquelles ils sont autorisés à accéder.

### 5.8. API Livraisons

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `GET` | `/deliveries/` | Lister les livraisons | Connecté |
| `POST` | `/deliveries/` | Créer le suivi d'une livraison | Autorisé |
| `GET` | `/deliveries/{id}/` | Consulter une livraison | Connecté |
| `PATCH` | `/deliveries/{id}/` | Modifier son suivi | Autorisé |
| `POST` | `/deliveries/{id}/mark-delivered/` | Marquer comme livrée | Autorisé |
| `POST` | `/deliveries/{id}/mark-failed/` | Marquer comme échec | Autorisé |

Règles :
- Une commande possède au maximum une livraison.
- Les coûts et frais facturés doivent être positifs ou nuls.
- Une livraison marquée `livree` doit avoir une date de livraison.
- Seules les commandes livrées et non annulées entrent dans les calculs de bénéfices.

### 5.9. API Dépenses

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `GET` | `/expenses/` | Lister les dépenses | Admin |
| `POST` | `/expenses/` | Ajouter une dépense | Admin |
| `GET` | `/expenses/{id}/` | Consulter une dépense | Admin |
| `PATCH` | `/expenses/{id}/` | Modifier une dépense | Admin |
| `DELETE` | `/expenses/{id}/` | Supprimer une dépense | Admin |

Une dépense contient une date, un libellé et un montant supérieur ou égal à zéro.

### 5.10. API Statistiques et tableau de bord

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `GET` | `/dashboard/summary/` | Résumé général | Admin |
| `GET` | `/dashboard/stock-alerts/` | Alertes de stock | Connecté |
| `GET` | `/dashboard/pending-orders/` | Commandes en attente | Connecté |
| `GET` | `/reports/summary/` | CA, bénéfice et dépenses sur une période | Admin |
| `GET` | `/reports/products/` | Quantités vendues et bénéfices par produit | Admin |
| `GET` | `/reports/orders/` | Bénéfices par commande | Admin |
| `GET` | `/reports/monthly/` | Résumé mensuel | Admin |

Paramètres de période :
- `?start_date=2026-01-01`
- `?end_date=2026-01-31`

Les rapports et l'export attendent les deux dates au format `YYYY-MM-DD` et limitent la période à un an. Le tableau de bord utilise le mois en cours par défaut.

Formules à appliquer :

```text
Chiffre d'affaires =
  somme des quantités × prix de vente - remises + frais de livraison facturés

Bénéfice brut =
  somme des quantités × (prix de vente - coût d'achat)
  - remises + frais de livraison facturés - coût de livraison

Bénéfice net =
  bénéfice brut - dépenses
```

Ne compter que les commandes livrées et non annulées. Agréger les livraisons séparément des lignes de commande afin de ne pas compter plusieurs fois les frais de livraison. Les remises d'une commande sont réparties au prorata des ventes de ses produits dans le rapport par produit.

### 5.11. API Export Excel

| Méthode | Route | Fonction | Accès |
|---|---|---|---|
| `GET` | `/exports/excel/` | Télécharger un rapport Excel | Admin |

Paramètres :
- `start_date`
- `end_date`

Le fichier contient les feuilles :
1. Résumé : période, commandes livrées, chiffre d'affaires, bénéfice brut, dépenses et bénéfice net.
2. Produits : quantités vendues, chiffre d'affaires et bénéfice par produit.
3. Stock : stock actuel et produits sous le seuil.
4. Dépenses : détail des dépenses de la période.

L'export Excel produit les quatre feuilles `Résumé`, `Produits`, `Stock` et `Dépenses`.

Sécurité :
- Valider les dates et limiter la période à un an.
- Neutraliser les cellules pouvant être interprétées comme des formules Excel (`=`, `+`, `-`, `@`).
- Réserver l'export à l'administrateur.
- Journaliser l'utilisateur, la date et la période exportée.
- Utiliser `Cache-Control: no-store`.

## 6. Organisation Django recommandée

Conserver les applications métier prévues dans le projet :

```text
GestionStock/
├── config/
│   ├── settings/
│   └── urls.py
├── apps/
│   ├── accounts/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   └── urls.py
│   ├── catalog/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── sales/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py
│   │   └── urls.py
│   ├── inventory/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py
│   │   └── urls.py
│   ├── finance/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py
│   │   └── urls.py
│   └── core/
│       ├── views.py
│       └── urls.py
└── ...
```

Ajouter `djangorestframework` aux dépendances et `rest_framework` dans `INSTALLED_APPS`.

Dans `config/urls.py`, inclure les routes de chaque application sous le préfixe `/api/v1/`.

### Responsabilités du code

- `models.py` : structure et contraintes des données.
- `serializers.py` : validation et conversion JSON.
- `views.py` : réception des requêtes et réponses HTTP.
- `permissions.py` : vérification des rôles et accès.
- `services.py` : opérations métier importantes (confirmation de commande, mouvement de stock, calculs).
- `selectors.py` : lectures et requêtes de données.
- `urls.py` : déclaration des endpoints.

Les vues doivent rester courtes. Les opérations financières et de stock ne doivent pas être calculées directement dans les vues.

## 7. Ordre de développement des API

Développer et tester les API dans cet ordre :

- [ ] **Étape 1 — Environnement API** : installer DRF, configurer les URLs, JSON, authentification et gestion des erreurs.
- [ ] **Étape 2 — Comptes** : modèle utilisateur personnalisé, login, logout, profil, rôles et permissions.
- [ ] **Étape 3 — Catalogue** : catégories, fournisseurs et produits.
- [ ] **Étape 4 — Stock** : consultation, mouvements d'entrée, pertes, calcul du stock et alertes.
- [ ] **Étape 5 — Ventes** : clients, commandes, lignes, confirmation et annulation.
- [ ] **Étape 6 — Livraisons** : suivi et changement de statut.
- [ ] **Étape 7 — Finance** : dépenses, bénéfices et statistiques.
- [ ] **Étape 8 — Exports** : génération du fichier Excel.
- [ ] **Étape 9 — Tests de sécurité** : permissions, accès aux objets, validation et concurrence.
- [ ] **Étape 10 — Déploiement** : Docker, serveur web, HTTPS, sauvegardes et supervision.

Pour la demande actuelle, l'application reste en développement local sur SQLite. Docker et le passage à PostgreSQL sont reportés à une étape ultérieure.

## 8. Tests obligatoires

Pour chaque endpoint, tester :
- un utilisateur non connecté ;
- un vendeur ;
- un administrateur ;
- des données valides ;
- des données invalides ;
- l'accès à une ressource appartenant à un autre utilisateur, si le périmètre est limité par utilisateur.

Tests métier particulièrement importants :
- [ ] Impossible de créer un produit avec un prix négatif.
- [ ] Un vendeur ne reçoit jamais le prix d'achat.
- [ ] Impossible de sortir plus d'articles que le stock disponible.
- [ ] Une commande confirmée ne retire le stock qu'une seule fois.
- [ ] Deux ventes simultanées du dernier article ne peuvent pas toutes les deux réussir.
- [ ] Un mouvement de stock ne peut pas être modifié ou supprimé.
- [ ] Une commande annulée ne compte pas dans les bénéfices.
- [ ] Une livraison est comptée une seule fois dans les frais et bénéfices.
- [ ] Seul l'admin peut consulter les dépenses, bénéfices et exports.
- [ ] Un utilisateur ne peut pas s'attribuer le rôle admin.

## 9. Déploiement en production

### Configuration

- Configurer les variables secrètes dans `.env`, jamais dans Git.
- Utiliser PostgreSQL avec un compte applicatif aux droits minimaux.
- Définir `DEBUG=False` et `ALLOWED_HOSTS`.
- Activer HTTPS et les cookies sécurisés.
- Configurer CORS uniquement si un frontend sur une autre origine en a réellement besoin.
- Garder PostgreSQL sur le réseau interne Docker ; ne pas publier le port 5432.
- Exposer uniquement Nginx ou Caddy sur les ports web.
- Configurer les volumes `media` et `staticfiles`.
- Prévoir des sauvegardes PostgreSQL chiffrées et tester leur restauration.

### Commandes de mise en ligne (à adapter au projet)

```bash
docker compose pull
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose exec web python manage.py check --deploy
```

Créer le compte administrateur avec :

```bash
docker compose exec web python manage.py createsuperuser
```

### Vérifications après déploiement

- [ ] Le site est accessible en HTTPS.
- [ ] `/api/v1/` répond correctement.
- [ ] Les endpoints privés refusent les utilisateurs non connectés.
- [ ] Les rôles admin et vendeur sont bien appliqués.
- [ ] Les uploads de photos fonctionnent.
- [ ] L'export Excel fonctionne uniquement pour l'admin.
- [ ] Les erreurs ne révèlent ni secrets ni traces techniques.
- [ ] Les sauvegardes sont exécutées et une restauration a été testée.

## 10. Points à décider avant le développement

Le schéma SQL fourni constitue une bonne base, mais certains choix doivent être harmonisés avec les règles du projet :

1. **Identifiants publics :** le schéma SQL fourni utilise des identifiants entiers. Le projet prévoit des UUID publics dans les URLs. Ajouter un champ UUID unique aux ressources exposées ou adopter un modèle équivalent.
2. **Historique des commandes :** le schéma SQL fourni met `ON DELETE CASCADE` sur `LigneCommande`. Pour préserver l'historique, ne pas supprimer une commande et revoir cette cascade.
3. **Suppression des mouvements :** l'API doit interdire toute modification ou suppression d'un mouvement.
4. **Dépenses :** le modèle est indiqué comme facultatif dans le SQL, mais il est nécessaire au calcul du bénéfice net.
5. **Droits vendeur :** décider précisément si le vendeur peut enregistrer les entrées, pertes, livraisons et modifier les produits.
6. **Authentification :** commencer avec les sessions Django si l'interface reste dans le même projet. Ajouter des jetons uniquement si un client séparé le nécessite.

## 11. Critère de fin

Le travail API sera considéré comme terminé lorsque :

- chaque module dispose de ses endpoints ;
- les validations et permissions sont testées ;
- le stock ne peut pas devenir négatif à cause de ventes concurrentes ;
- les calculs financiers sont vérifiés ;
- l'export Excel fonctionne ;
- l'application est déployée en HTTPS ;
- les sauvegardes et la restauration sont opérationnelles.

---

**Principe de réalisation :** construire les API progressivement, une application Django à la fois. Ne pas développer toutes les routes avant d'avoir testé les opérations métier essentielles.
