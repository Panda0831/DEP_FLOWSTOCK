# Déploiement de FlowStock sur Render

Le [Blueprint racine](../../render.yaml) définit l’API Django construite avec
[`Bakend/Dockerfile`](../../Bakend/Dockerfile), sa base PostgreSQL et le site
statique Expo Web, sur les plans gratuits de Render. La configuration sert à
un essai ou une démonstration. Elle ne convient pas à des données métier à
conserver : la base gratuite expire après 30 jours, le service web s’endort
après 15 minutes sans trafic et les fichiers envoyés (photos des produits)
restent sur un disque éphémère.

## Créer les services

1. Connectez votre compte GitHub à Render et sélectionnez le dépôt FlowStock.
   Si le dépôt privé n’apparaît pas, demandez au propriétaire ou à un
   administrateur du dépôt d’autoriser l’application GitHub de Render pour ce
   dépôt. Une fois l’accès accordé, un collaborateur peut créer et gérer le
   Blueprint selon les droits Render de son compte.
2. Ouvrez le [lien de déploiement Render](https://render.com/deploy?repo=https://github.com/Panda0831/DEP_FLOWSTOCK), puis confirmez la création de `flowstock-api`,
   `flowstock-db` et `flowstock-web`. Render construit l’image API depuis le
   Dockerfile du dépôt; le conteneur collecte les fichiers statiques et applique
   les migrations au démarrage. Le front est exporté en fichiers statiques et
   publié séparément.
3. Attendez le premier déploiement. Le démarrage applique les migrations, puis
   l’API répond sur `https://flowstock-api.onrender.com/healthz/`.
4. Le site Expo web est construit par Render avec
   `EXPO_PUBLIC_API_URL=https://flowstock-api.onrender.com/api/v1` et publié à
   `https://flowstock-web.onrender.com`. L’URL de l’API est également visible
   dans son tableau de bord Render. Pour publier l’application native iOS ou
   Android, utilisez Expo EAS séparément; le site statique Render ne génère pas
   les applications mobiles.

Le bouton de déploiement désactive les redéploiements automatiques afin que les
créations de service indépendantes ne redéploient pas toutes à chaque commit.
Pour publier une nouvelle version, déclenchez un déploiement manuel dans Render.
Les secrets sont générés par Render et restent dans ses variables
d’environnement; aucun secret n’est à ajouter au dépôt.

L’API autorise l’origine web `flowstock-web.onrender.com` pour CORS et CSRF.
Si vous renommez le site ou ajoutez un domaine personnalisé, mettez à jour
`CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` et la valeur
`EXPO_PUBLIC_API_URL` dans le Blueprint, puis redéployez les services.

## Premier compte administrateur

L’inscription publique crée un compte vendeur. Pour créer le premier compte
administrateur, utilisez la connexion externe PostgreSQL fournie dans l’onglet
**Connect** de `flowstock-db`, depuis un environnement local qui a les
dépendances backend installées. La connexion externe de Render requiert TLS.
Définissez temporairement `DATABASE_URL`, `DJANGO_SECRET_KEY` (copiée depuis les
variables du service web) et `ALLOWED_HOSTS=flowstock-api.onrender.com`, puis
lancez depuis `Bakend/` :

```bash
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py createsuperuser
```

Retirez ensuite ces valeurs de l’environnement local. Ne copiez pas l’URL de
base ni la clé secrète dans le dépôt ou dans un ticket.

## Pour un déploiement durable

Le plan gratuit de Render est fait pour les essais : le service gratuit utilise
512 Mo de mémoire, s’endort après 15 minutes d’inactivité et peut redémarrer.
La base PostgreSQL gratuite est limitée à 1 Go, sans sauvegardes, et expire au
bout de 30 jours (avec 14 jours pour la passer à une offre payante avant sa
suppression). Les fichiers écrits localement, notamment les photos, disparaissent
quand le service redémarre, s’endort ou est redéployé. [Détails officiels sur
les limites du Free Tier](https://render.com/docs/free).

Avant d’utiliser FlowStock avec des données réelles, passez PostgreSQL à un plan
payant qui ne s’expire pas et configurez un stockage persistant des images, ou
mettez l’API sur une offre payante avec disque persistant. Le prix du plus petit
PostgreSQL payant affiché actuellement commence à 6 USD/mois; le calcul total
inclut aussi le service web et le stockage éventuel. [Tarifs Render](https://render.com/pricing).

Cette préparation ne crée pas les services Render et n’effectue aucun
déploiement dans un compte Render.
