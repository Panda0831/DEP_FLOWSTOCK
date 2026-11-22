# StockFlow Mobile

Application Expo / React Native de StockFlow. Le client est relié au backend complet de `origin/main`, qui utilise l’authentification par session Django et expose les modules de catalogue, stock, ventes et finances.

## Démarrer le front

```bash
npm install
cp .env.example .env
npm start
```

Renseignez `EXPO_PUBLIC_API_URL` avec l’adresse du backend complète, préfixée par `/api/v1` :

- navigateur ou simulateur iOS sur le même ordinateur : `http://127.0.0.1:8000/api/v1`
- émulateur Android : `http://10.0.2.2:8000/api/v1`
- téléphone physique : `http://<adresse-IP-du-PC>:8000/api/v1`

Pour un téléphone, Django doit écouter sur `0.0.0.0:8000` et `ALLOWED_HOSTS` doit contenir l’adresse IP du PC. Le client récupère le cookie CSRF de Django et conserve le cookie de session dans SecureStore sur mobile. Sur le web, le navigateur gère le cookie de session; l’API doit autoriser l’origine Expo avec les credentials.

## Backend requis

Le dossier `../../Bakend` de cette branche contient le module de comptes JWT de `origin/feature/acount-module`. Il n’expose pas les routes de produits, stock, commandes, livraisons ou finances et son authentification est incompatible avec ce client. Depuis la racine du dépôt, créez un checkout séparé du backend complet :

```bash
git worktree add ../FlowStock-backend-main origin/main
cd ../FlowStock-backend-main/Bakend
```

Suivez le guide `Bakend/README.md` de ce checkout pour configurer et démarrer Django. L’URL configurée dans `.env` doit pointer vers ce serveur complet.

## Routes utilisées

Toutes les routes ci-dessous sont relatives au préfixe `/api/v1`.

| Fonction | Routes |
| --- | --- |
| Comptes | `POST /auth/signup/`, `POST /auth/login/`, `POST /auth/logout/`, `GET/PATCH /auth/me/` |
| Mots de passe | `POST /auth/password/change/`, `POST /auth/password/reset/request/`, `POST /auth/password/reset/confirm/` |
| Catalogue | CRUD `/products/`, `/categories/`, `/suppliers/` |
| Clients et ventes | CRUD `/clients/`, `/orders/`; actions `POST /orders/{id}/confirm/` et `/orders/{id}/cancel/` |
| Stock | `GET /stock/`, `GET /stock/alerts/`, `GET /movements/`, `POST /movements/entries/`, `POST /movements/losses/` |
| Livraisons | CRUD `/deliveries/`; actions `POST /deliveries/{id}/mark-delivered/` et `POST /deliveries/{id}/mark-failed/` |
| Finances | CRUD `/expenses/`; tableaux de bord `/dashboard/summary/`, `/dashboard/pending-orders/`; rapports `/reports/summary/`, `/reports/products/`, `/reports/orders/`; export `/exports/excel/` |

Le backend applique les permissions par rôle. Les formulaires du front limitent les actions d’administration, et le serveur reste l’autorité pour chaque permission.
