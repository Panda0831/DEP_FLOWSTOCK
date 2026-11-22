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

Le dossier `../../Bakend` expose les modules de comptes, catalogue, stock,
achats, ventes, livraisons et paiements. Suivez `Bakend/README.md` pour
installer les dépendances et démarrer l'API. L’URL configurée dans `.env` doit
pointer vers ce serveur et se terminer par `/api/v1`.

## Routes utilisées

Toutes les routes ci-dessous sont relatives au préfixe `/api/v1`.

| Fonction | Routes |
| --- | --- |
| Comptes | `POST /auth/signup/`, `POST /auth/login/`, `POST /auth/logout/`, `GET/PATCH /auth/me/` |
| Mots de passe | `POST /auth/password/change/`, `POST /auth/password/reset/request/`, `POST /auth/password/reset/confirm/` |
| Catalogue | CRUD `/products/`, `/categories/`, `/suppliers/` |
| Clients et ventes | CRUD `/clients/`, `/orders/`; actions `POST /orders/{id}/confirm/` et `/orders/{id}/cancel/` |
| Stock | `GET /stock/`, `GET /stock/alerts/`, `GET /movements/`, `POST /movements/entries/`, `POST /movements/losses/` |
| Paiements | Paiements partiels pour commandes et achats via `POST /payments/` |
| Achats | `GET/POST /purchases/`, réception partielle `/purchases/{id}/receive/`, historique `/purchase-receptions/` |
| Livraisons | CRUD `/deliveries/`; actions de préparation, expédition, livraison, échec/reprise et retour |
| Finances | CRUD `/expenses/`; tableaux de bord `/dashboard/summary/`, `/dashboard/pending-orders/`; rapports `/reports/summary/`, `/reports/products/`, `/reports/orders/`; export `/exports/excel/` |

Le backend applique les permissions par rôle. Les formulaires du front limitent les actions d’administration, et le serveur reste l’autorité pour chaque permission.
