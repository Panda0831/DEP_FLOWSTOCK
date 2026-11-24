# FlowStock API

API Django utilisée par l'application mobile/web FlowStock. Elle fournit les
comptes, le catalogue, le stock, les ventes, les livraisons, les dépenses et
les rapports sous le préfixe `/api/v1/`.

## Démarrage local

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Le client Expo doit utiliser `http://127.0.0.1:8000/api/v1` en local.

## Production

Le déploiement exige les variables suivantes :

```dotenv
DJANGO_SECRET_KEY=<secret aléatoire long>
DJANGO_DEBUG=False
ALLOWED_HOSTS=api.example.com
DATABASE_URL=postgresql://flowstock:<mot-de-passe>@<hôte>:5432/flowstock
ACTIVER_DOCUMENTATION_API=False
```

Si le client web est servi depuis une autre origine, ajoutez les origines HTTPS
exactes dans `CORS_ALLOWED_ORIGINS` et `CSRF_TRUSTED_ORIGINS`. Pour des sites
réellement cross-site, configurez les deux variables `*_SAMESITE=None`.

Avant la mise en ligne :

```bash
python manage.py check --deploy --settings=config.settings.prod
python manage.py makemigrations --check --dry-run --settings=config.settings.prod
python manage.py migrate --settings=config.settings.prod
python manage.py collectstatic --noinput --settings=config.settings.prod
gunicorn --bind 0.0.0.0:${PORT:-8000} config.wsgi:application
```

La sonde de disponibilité est disponible sur `/healthz/`.

## CI et livraison de l'image backend

GitHub Actions exécute les contrôles backend et mobile sur les push et pull
requests. Un push d'une étiquette de version au format `v*` publie l'image du
backend dans GitHub Container Registry sous `ghcr.io/<propriétaire>/flowstock-api`,
avec les variantes `linux/amd64` et `linux/arm64`. Les autres événements
construisent l'image sans la publier.

Exemple de publication après validation de la version :

```bash
git tag v1.0.0
git push origin v1.0.0
```

L'image contient l'application, pas la base PostgreSQL ni les secrets. Pour le
déploiement VPS par Docker Compose, la configuration de production et les
secrets restent dans un fichier `.env` créé directement sur le serveur; Compose
construit `DATABASE_URL` à partir des variables PostgreSQL. Le job de livraison
SSH ne s’exécute qu’après la publication réussie d’un tag `v*` et si la variable
GitHub `VPS_DEPLOY_ENABLED=true` est activée. La procédure, les secrets GitHub
requis, les prérequis du serveur et les limites sont décrits dans
[`deploy/vps/README.md`](../deploy/vps/README.md). Aucun VPS n’est choisi ou
provisionné par le dépôt.
