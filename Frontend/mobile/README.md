# StockFlow Mobile

Application Expo / React Native du projet StockFlow.

## Démarrer le front

```bash
npm install
cp .env.example .env
npm start
```

Renseignez `EXPO_PUBLIC_API_URL` dans `.env` avec l’adresse du backend et le préfixe `/api/v1`. Utilisez `http://10.0.2.2:8000/api/v1` sur l’émulateur Android, ou l’adresse IP locale de l’ordinateur sur un téléphone physique. `localhost` convient au navigateur ou au simulateur iOS sur le même ordinateur. Pour Expo Go sur un téléphone, le serveur Django doit écouter sur `0.0.0.0:8000` et `ALLOWED_HOSTS` doit inclure l’adresse IP locale du PC.

Le backend JWT de `origin/feature/acount-module` est inclus dans ce checkout, sous `../../Bakend`. Son guide de démarrage est dans [`Bakend/README.md`](../../Bakend/README.md). Le backend complet de `origin/main` expose un contrat différent basé sur les sessions Django ; il n’est pas interchangeable avec le client JWT de cette app.

## Routes API reliées

Toutes les routes utilisent le préfixe configuré dans `EXPO_PUBLIC_API_URL`.

| Usage | Méthode et route | Contrat utilisé |
| --- | --- | --- |
| Connexion | `POST /auth/login/` | `email`, `mot_de_passe`; renvoie `access`, `refresh`, `utilisateur` |
| Profil / restauration de session | `GET /auth/me/` | En-tête `Authorization: Bearer <access>` |
| Renouvellement JWT | `POST /auth/token/refresh/` | `refresh`; renvoie la nouvelle paire de jetons |
| Déconnexion | `POST /auth/logout/` | Bearer access + corps `{ "refresh": "…" }` |
| Demande de réinitialisation | `POST /auth/password/reset/request/` | `email`; réponse générique pour ne pas révéler si le compte existe |
| Confirmation de réinitialisation | `POST /auth/password/reset/confirm/` | `uid`, `token`, `nouveau_mot_de_passe`, `confirmation_nouveau_mot_de_passe` |
| Changement obligatoire du mot de passe | `POST /auth/password/change/` | `ancien_mot_de_passe`, `nouveau_mot_de_passe`, `confirmation_nouveau_mot_de_passe` |

Les jetons sont enregistrés dans SecureStore sur iOS/Android et dans `sessionStorage` sur le web. Une session existante est restaurée avec `/auth/me/`; si l’access a expiré, le front appelle `/auth/token/refresh/`.

La branche `feature/acount-module` ne propose pas d’inscription publique : `POST /users/` est réservé aux administrateurs. Le lien « Demander un accès » l’indique donc à l’utilisateur. Pour que les liens reçus ouvrent la route `/reset-password?uid=…&token=…`, configurez `URL_FRONTEND_REINITIALISATION` dans le backend (par exemple `flowstock://reset-password` pour une app installée, ou une URL web de développement). En développement, le backend écrit les liens dans sa sortie console selon sa configuration e-mail.

Pour le web, le navigateur exige que le backend autorise l’origine Expo via CORS. Expo Go sur iOS/Android n’est pas soumis à cette restriction du navigateur.
