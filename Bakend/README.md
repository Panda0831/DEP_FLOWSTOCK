# FlowStock — Backend Django

FlowStock est une API Django REST limitée au **module des utilisateurs** : comptes avec identifiant UUID, rôles, authentification JWT, profils, réinitialisation de mots de passe et journal immuable des événements de sécurité.

- Django 5.2
- Django REST Framework 3.18
- Simple JWT 5.5
- PostgreSQL
- Pytest / pytest-django
- drf-spectacular pour OpenAPI
- Python recommandé : **3.13**

Le dépôt ne contient pas de frontend ni de modules de stock/vente. Les chemins ci-dessous sont relatifs à ce README.

## Sommaire

1. [Architecture](#architecture)
2. [Prérequis](#prérequis)
3. [Installation depuis zéro](#installation-depuis-zéro)
4. [Installation et démarrage de PostgreSQL](#installation-et-démarrage-de-postgresql)
5. [Création des rôles et bases PostgreSQL](#création-des-rôles-et-bases-postgresql)
6. [Configuration des variables d’environnement](#configuration-des-variables-denvironnement)
7. [Migrations Django](#migrations-django)
8. [Démarrage du serveur](#démarrage-du-serveur)
9. [Création d’un administrateur](#création-dun-administrateur)
10. [API et documentation](#api-et-documentation)
11. [Tests](#tests)
12. [Qualité, sécurité et documentation](#qualité-sécurité-et-documentation)
13. [Déploiement en production](#déploiement-en-production)
14. [Commandes utiles](#commandes-utiles)
15. [Dépannage](#dépannage)

## Architecture

```text
FlowStock/
├── README.md
└── Bakend/
    ├── manage.py                 # Commandes Django
    ├── pyproject.toml            # pytest, coverage, Ruff et Bandit
    ├── requirements.txt          # Image globale historique de l’environnement
    ├── requirements/
    │   ├── base.txt              # Dépendances applicatives
    │   ├── dev.txt               # Outils de développement et tests
    │   └── prod.txt             # Dépendances de production
    ├── config/
    │   ├── urls.py               # Routes globales
    │   ├── asgi.py
    │   ├── wsgi.py
    │   └── settings/
    │       ├── base.py           # Configuration commune
    │       ├── dev.py            # Développement
    │       ├── test.py           # Tests PostgreSQL
    │       └── prod.py           # Production stricte
    ├── apps/
    │   ├── conftest.py           # Fixtures pytest communes
    │   ├── core/                 # Pagination, exceptions, middleware, limites
    │   └── accounts/             # Modèle utilisateur, JWT, comptes et journal
    └── docs/
        └── schema.yml            # Schéma OpenAPI versionné
```

Toutes les commandes suivantes doivent être exécutées depuis `Bakend/`, sauf indication contraire.

```bash
cd /home/noctis/Videos/FlowStock/Bakend
```

Adaptez ce chemin sur Windows ou macOS.

## Prérequis

### Logiciels obligatoires

- Python **3.13 recommandé** ; Python 3.12 ou 3.13 est préférable à une nouvelle version non testée.
- PostgreSQL local ou distant.
- `pip` et `venv`.
- Git.
- `psql`, requis pour initialiser PostgreSQL.

### Vérifier les outils

```bash
python3 --version
python3 -m pip --version
python3 -m venv --help
psql --version
```

Sur Ubuntu/Debian, l’installation peut nécessiter :

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev \
  postgresql postgresql-contrib libpq-dev build-essential
```

Sur macOS avec Homebrew :

```bash
brew install python@3.13 postgresql@16
brew services start postgresql@16
```

Sur Windows, utilisez Python 3.13, PostgreSQL et PowerShell. Les sections PostgreSQL utilisent `psql` et sont également applicables après avoir ajouté `psql` au `PATH`.

### Dépendances principales

- Développement/tests : `-r requirements/dev.txt`
- Production : `-r requirements/prod.txt`
- La liste globale `requirements.txt` est un instantané complet de l’environnement système local ; elle n’est pas la méthode d’installation recommandée.

## Installation depuis zéro

### 1. Ouvrir le dossier backend

```bash
cd /home/noctis/Videos/FlowStock/Bakend
```

### 2. Créer un environnement virtuel

Linux/macOS :

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell :

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Invite de commandes :

```bat
py -3.13 -m venv .venv
.venv\Scripts\activate.bat
```

Après activation, la commande suivante doit afficher Python depuis `.venv` :

```bash
python --version
which python
```

Sur Windows :

```powershell
python --version
where.exe python
```

### 3. Mettre à jour pip et installer les dépendances

Pour développer et exécuter les tests :

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements/dev.txt
```

Pour l’exécution serveur uniquement :

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements/prod.txt
```

Pour installer les deux ensembles localement :

```bash
python -m pip install -r requirements/dev.txt
python -m pip install -r requirements/prod.txt
```

### 4. Vérifier Django

```bash
python -m django --version
python manage.py --help
```

## Installation et démarrage de PostgreSQL

### Ubuntu/Debian

```bash
sudo systemctl enable postgresql
sudo systemctl start postgresql
sudo systemctl status postgresql
sudo -u postgres psql
```

### macOS

```bash
brew services start postgresql@16
psql postgres
```

### Docker, si Docker est utilisé

Aucun fichier Docker n’est inclus dans le dépôt. Voici une configuration locale fonctionnelle :

```bash
docker run --name stockflow-postgres \
  --publish 5432:5432 \
  --env POSTGRES_DB=postgres \
  --env POSTGRES_PASSWORD=postgres-admin-temporaire \
  --detach postgres:16
```

Pour arrêter et redémarrer :

```bash
docker stop stockflow-postgres
docker start stockflow-postgres
docker exec -it stockflow-postgres psql -U postgres
```

Ne conservez pas de mot de passe administrateur évident en production.

## Création des rôles et bases PostgreSQL

Il est recommandé d’utiliser deux rôles PostgreSQL :

- `stockflow_app` : accès normal à la base applicative, sans droits super-utilisateur.
- `stockflow_test` : peut créer/supprimer la base temporaire du test runner.

Ouvrez `psql` comme administrateur PostgreSQL :

```bash
sudo -u postgres psql
```

Exécutez :

```sql
CREATE ROLE stockflow_app
  LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  PASSWORD 'remplacez-ce-mot-de-passe-applicatif';

CREATE ROLE stockflow_test
  LOGIN NOSUPERUSER CREATEDB NOCREATEROLE
  PASSWORD 'remplacez-ce-mot-de-passe-de-test';

CREATE DATABASE stockflow
  OWNER stockflow_app
  ENCODING 'UTF8';

\q
```

### Connexion de vérification

```bash
psql -h localhost -p 5432 -U stockflow_app -d stockflow
```

Puis :

```sql
SELECT current_user, current_database();
\q
```

Si PostgreSQL demande l’authentification sur Linux, vérifiez `pg_hba.conf` et configurez une méthode adaptée à votre environnement. Pour le développement local, le mode `scram-sha-256` est recommandé.

### Gestion des droits

Pour vérifier les droits :

```sql
\du
\l
```

Pour modifier les mots de passe :

```sql
ALTER ROLE stockflow_app PASSWORD 'nouveau-mot-de-passe-long';
ALTER ROLE stockflow_test PASSWORD 'nouveau-mot-de-passe-long';
```

Pour supprimer entièrement l’environnement local :

```sql
DROP DATABASE IF EXISTS stockflow;
DROP ROLE IF EXISTS stockflow_app;
DROP ROLE IF EXISTS stockflow_test;
```

Arrêtez-vous ici si les bases existantes contiennent des données importantes : `DROP DATABASE` est destructif.

## Configuration des variables d’environnement

### Copier le modèle

Linux/macOS :

```bash
cp .env.example .env
chmod 600 .env
```

Windows PowerShell :

```powershell
Copy-Item .env.example .env
```

Windows Invite de commandes :

```bat
copy .env.example .env
```

`.env` est lu depuis `Bakend/.env` et doit être ignoré par Git. Ne committez aucune valeur réelle.

### Générer les clés secrètes

Deux clés distinctes sont obligatoires : `SECRET_KEY` et `JWT_CLE_SIGNATURE`.

```bash
python - <<'PY'
from django.core.management.utils import get_random_secret_key
import secrets
print('SECRET_KEY=' + get_random_secret_key())
print('JWT_CLE_SIGNATURE=' + secrets.token_urlsafe(64))
PY
```

La clé JWT doit contenir **au moins 50 caractères** et être différente de `SECRET_KEY`.

### Exemple de `.env` pour le développement

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.dev

SECRET_KEY=<clé Django de 50 caractères ou plus générée ci-dessus>
JWT_CLE_SIGNATURE=<clé JWT distincte de plus de 50 caractères>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

BASE_DE_DONNEES_URL=
BDD_HOTE=localhost
BDD_PORT=5432
BDD_NOM=stockflow
BDD_UTILISATEUR=stockflow_app
BDD_MOT_DE_PASSE=<mot de passe du rôle applicatif>

BDD_TEST_UTILISATEUR=stockflow_test
BDD_TEST_MOT_DE_PASSE=<mot de passe du rôle de test>

NOMBRE_PROXIES_DE_CONFIANCE=0
ACTIVER_DOCUMENTATION_API=True

EMAIL_HOST=localhost
EMAIL_PORT=25
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=False
EMAIL_FROM=StockFlow <noreply@localhost>
URL_FRONTEND_REINITIALISATION=http://localhost:3000/reinitialiser-mot-de-passe

CACHE_URL=
```

En développement, `dev.py` force le backend console pour les e-mails : les liens/résultats apparaissent dans le terminal du serveur.

### Variables obligatoires

| Variable | Description |
|---|---|
| `SECRET_KEY` | Clé secrète Django. Obligatoire. |
| `JWT_CLE_SIGNATURE` | Clé HS256 des jetons JWT, distincte de `SECRET_KEY`, au moins 50 caractères. |
| `BDD_HOTE` | Hôte PostgreSQL ; défaut du modèle : `localhost`. |
| `BDD_PORT` | Port PostgreSQL ; par défaut `5432`. |
| `BDD_NOM` | Nom de la base applicative. |
| `BDD_UTILISATEUR` | Utilisateur PostgreSQL applicatif. |
| `BDD_MOT_DE_PASSE` | Mot de passe PostgreSQL applicatif. |
| `BDD_TEST_UTILISATEUR` | Utilisateur PostgreSQL autorisé à créer une base temporaire. |
| `BDD_TEST_MOT_DE_PASSE` | Mot de passe de l’utilisateur de test. |

### Variables optionnelles ou conditionnelles

| Variable | Valeur par défaut | Utilisation |
|---|---:|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` via `manage.py` | Peut sélectionner une configuration manuelle. |
| `DEBUG` | `False` | Doit rester désactivé en production. |
| `ALLOWED_HOSTS` | Liste vide | Séparées par des virgules ; obligatoire en production. |
| `BASE_DE_DONNEES_URL` | vide | Alternative PostgreSQL sous forme `postgresql://...`. |
| `NOMBRE_PROXIES_DE_CONFIANCE` | `0` | Nombre de proxies de confiance pour `NUM_PROXIES`. |
| `ACTIVER_DOCUMENTATION_API` | `False` dans la base | Swagger sur `/api/v1/docs/`; activé par défaut en `dev`/`test`. |
| `EMAIL_HOST` | `localhost` | Serveur SMTP en production. |
| `EMAIL_PORT` | `25` | Port SMTP. |
| `EMAIL_HOST_USER` | vide | Identifiant SMTP. |
| `EMAIL_HOST_PASSWORD` | vide | Mot de passe SMTP. |
| `EMAIL_USE_TLS` | `False` | Activer TLS SMTP. |
| `EMAIL_FROM` | `StockFlow <noreply@localhost>` | Expéditeur par défaut. |
| `URL_FRONTEND_REINITIALISATION` | vide | Base utilisée pour les liens de réinitialisation. |
| `CACHE_URL` | obligatoire en production | Cache partagé Django. |

### Connexion PostgreSQL via URL

Une URL peut remplacer les variables `BDD_*`. Cette URL doit impérativement être PostgreSQL :

```dotenv
BASE_DE_DONNEES_URL=postgresql://stockflow_app:mot-de-passe@localhost:5432/stockflow
```

Si `BASE_DE_DONNEES_URL` est renseignée, les variables `BDD_HOTE`, `BDD_NOM`, `BDD_UTILISATEUR` et `BDD_MOT_DE_PASSE` ne sont pas utilisées pour la connexion. URL-encodez les caractères spéciaux du mot de passe.

## Migrations Django

### Premier démarrage

Le dépôt contient actuellement les modèles mais aucune application de migrations versionnée n’a été trouvée. Dans ce cas, initialisez-les avant la première migration :

```bash
python manage.py makemigrations apps.core apps.accounts
python manage.py makemigrations
python manage.py showmigrations
python manage.py migrate
```

Si un dossier `migrations/` existe déjà avec un historique versionné dans votre branche, utilisez seulement :

```bash
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

### Vérifications avant migration

```bash
python manage.py check --database default
python manage.py showmigrations
python manage.py sqlmigrate accounts 0001
```

Remplacez `0001` par le numéro réel généré.

### Créer une migration après une modification de modèle

```bash
python manage.py makemigrations accounts
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

### Annuler une migration

Le retour à un ancien état dépend des données existantes. Exemple vers une migration nommée `0001_initial` :

```bash
python manage.py migrate accounts 0001_initial
```

Pour annuler toutes les migrations d’une application dans un environnement jetable :

```bash
python manage.py migrate accounts zero
```

Ne supprimez pas les fichiers de migration pour “corriger” des erreurs sans avoir compris leur dépendance. Sauvegardez PostgreSQL avant toute migration d’exploitation.

### Sauvegarde PostgreSQL

Sauvegarde :

```bash
pg_dump -h localhost -U stockflow_app -d stockflow -Fc -f stockflow.dump
```

Restauration dans une base neuve :

```bash
createdb -h localhost -U postgres -O stockflow_app stockflow_restore
pg_restore -h localhost -U stockflow_app -d stockflow_restore --clean --if-exists stockflow.dump
```

## Démarrage du serveur

### Serveur HTTP de développement

```bash
python manage.py runserver
```

URL par défaut :

- API : `http://127.0.0.1:8000/api/v1/`
- Admin : `http://127.0.0.1:8000/admin/`
- Swagger : `http://127.0.0.1:8000/api/v1/docs/`
- Schéma JSON : `http://127.0.0.1:8000/api/v1/schema/`

Écoute sur toutes les interfaces :

```bash
python manage.py runserver 0.0.0.0:8000
```

Écoute sur un port personnalisé :

```bash
python manage.py runserver 127.0.0.1:8080
```

La documentation n’est exposée que si `ACTIVER_DOCUMENTATION_API=True`. Dans `dev.py`, elle vaut `True` par défaut.

### Serveur ASGI

Daphne ou Uvicorn ne sont pas inclus dans les fichiers de dépendances actuels. Avec Uvicorn installé :

```bash
python -m pip install uvicorn
DJANGO_SETTINGS_MODULE=config.settings.prod uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

## Création d’un administrateur

Après les migrations :

```bash
python manage.py createsuperuser
```

Entrez l’e-mail, le nom, le prénom puis le mot de passe. Le gestionnaire d’utilisateurs doit fournir tous les champs demandés par `UserManager`. Pour créer un super-utilisateur non interactif :

```bash
python manage.py shell -c "
from apps.accounts.models import Utilisateur
u = Utilisateur.objects.create_superuser(email='admin@exemple.test', nom='Admin', prenom='StockFlow', password='ChangezCeMotDePasse!2026')
print(u.email, u.uuid)
"
```

Ne conservez jamais ce mot de passe dans des scripts versionnés. Changer le mot de passe via l’API après la connexion initiale est recommandé.

## API et documentation

### Routeurs disponibles

| Fonction | Méthode | Route |
|---|---|---|
| Connexion | `POST` | `/api/v1/auth/login/` |
| Rafraîchir l’accès | `POST` | `/api/v1/auth/token/refresh/` |
| Mon profil | `GET` | `/api/v1/auth/me/` |
| Changer le mot de passe | `POST` | `/api/v1/auth/password/change/` |
| Demander une réinitialisation | `POST` | `/api/v1/auth/password/reset/request/` |
| Confirmer une réinitialisation | `POST` | `/api/v1/auth/password/reset/confirm/` |
| Déconnexion | `POST` | `/api/v1/auth/logout/` |
| Créer un utilisateur | `POST` | `/api/v1/users/` |
| Lister les utilisateurs | `GET` | `/api/v1/users/` |
| Consulter un utilisateur | `GET` | `/api/v1/users/{uuid}/` |
| Modifier un utilisateur | `PATCH` | `/api/v1/users/{uuid}/` |
| Désactiver un utilisateur | `POST` | `/api/v1/users/{uuid}/deactivate/` |

La majorité des routes nécessite un jeton `Bearer` d’accès. Les super-utilisateurs peuvent aussi avoir accès aux routes administratives selon les permissions métier.

### Connexion avec `curl`

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@exemple.test","password":"VotreMotDePasse!2026"}'
```

Extraire les jetons de la réponse puis exporter-les :

```bash
export ACCESS='remplacez-par-access-token'
export REFRESH='remplacez-par-refresh-token'
```

Profil connecté :

```bash
curl -i http://127.0.0.1:8000/api/v1/auth/me/ \
  -H "Authorization: Bearer $ACCESS"
```

Rafraîchir un jeton :

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/token/refresh/ \
  -H 'Content-Type: application/json' \
  -d "{\"refresh\":\"$REFRESH\"}"
```

Lister les utilisateurs :

```bash
curl -i 'http://127.0.0.1:8000/api/v1/users/?page=1&page_size=20' \
  -H "Authorization: Bearer $ACCESS"
```

Créer un utilisateur :

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/users/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"email":"vendeur@exemple.test","nom":"Rakoto","prenom":"Hery","telephone":"","role":"vendeur"}'
```

Déconnexion :

```bash
curl -i -X POST http://127.0.0.1:8000/api/v1/auth/logout/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $ACCESS" \
  -d "{\"refresh\":\"$REFRESH\"}"
```

### Limitation des requêtes

La configuration active des quotas par adresse/IP ou utilisateur, notamment :

- connexion : 10/minute ;
- connexion par e-mail : 5/15 minutes ;
- renouvellement : 30/minute ;
- déconnexion : 30/minute ;
- création : 30/minute ;
- demande de réinitialisation : 5/heure ;
- demande par e-mail : 3/heure ;
- confirmation : 10/heure ;
- changement de mot de passe : 5/heure.

L’activation des proxies doit correspondre à l’infrastructure réelle. Avec `NOMBRE_PROXIES_DE_CONFIANCE=0`, les adresses directement visibles sont utilisées.

## Tests

### Configuration PostgreSQL des tests

La configuration `config.settings.test` lit obligatoirement :

- `BDD_TEST_UTILISATEUR` ;
- `BDD_TEST_MOT_DE_PASSE`.

Le rôle doit avoir `CREATEDB`. Django crée alors une base temporaire similaire à `test_<BDD_NOM>`, puis la supprime.

Pour vérifier les permissions du rôle :

```sql
ALTER ROLE stockflow_test CREATEDB;
\du stockflow_test
```

Pour retirer uniquement cette permission après les tests :

```sql
ALTER ROLE stockflow_test NOCREATEDB;
```

Les tests ne doivent jamais être lancés avec les identifiants de production. Ils sont isolés dans une base temporaire, mais leur compte PostgreSQL reste distinctement configuré.

### Lancer toute la suite

Depuis `Bakend/` :

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest
```

Sous Windows PowerShell :

```powershell
$env:DJANGO_SETTINGS_MODULE='config.settings.test'
pytest
Remove-Item Env:\DJANGO_SETTINGS_MODULE
```

Sous Windows Invite de commandes :

```bat
set DJANGO_SETTINGS_MODULE=config.settings.test
pytest
set DJANGO_SETTINGS_MODULE=
```

Pytest est configuré dans `pyproject.toml` pour :

- trouver les fichiers `test_*.py` ;
- charger `config.settings.test` ;
- utiliser les modes stricts de configuration et de marqueurs.

### Tests ciblés

Un fichier :

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest apps/accounts/tests/test_connexion.py
```

Un dossier :

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest apps/accounts/tests/
```

Un test précis :

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest \
  apps/accounts/tests/test_connexion.py::test_nom_du_test
```

Pour obtenir les noms disponibles :

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest --collect-only -q
```

### Afficher la sortie détaillée

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest -vv
DJANGO_SETTINGS_MODULE=config.settings.test pytest -vv -s
```

### Arrêter au premier échec

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest -x
```

### Réutiliser la base de test

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest --reuse-db
```

À utiliser uniquement pour accélérer les cycles locaux. Pour repartir d’une base vierge :

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest --create-db
```

### Sortie courte ou sans capture

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest -q
DJANGO_SETTINGS_MODULE=config.settings.test pytest --no-capture
```

### Coverage

La couverture active les branches pour `apps.accounts` et `apps.core`; les tests eux-mêmes et les migrations sont exclus. Le seuil global configuré est de **95 %**.

Suite avec couverture :

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest --cov=apps --cov-report=term-missing --cov-report=html
```

Le rapport HTML est créé dans `htmlcov/index.html`.

Résumé seul :

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest --cov=apps.accounts --cov=apps.core --cov-report=term-missing
```

XML pour CI :

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest --cov=apps --cov-report=xml:coverage.xml --cov-report=term
```

Lancer le rapport après une suite déjà jouée :

```bash
coverage report --show-missing
coverage html
```

### Tests par groupe

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest apps/accounts/tests/test_connexion.py \
  apps/accounts/tests/test_rafraichissement.py \
  apps/accounts/tests/test_deconnexion.py

DJANGO_SETTINGS_MODULE=config.settings.test pytest apps/accounts/tests/test_creation_utilisateur.py \
  apps/accounts/tests/test_liste_utilisateurs.py \
  apps/accounts/tests/test_detail_utilisateur.py \
  apps/accounts/tests/test_modification_utilisateur.py \
  apps/accounts/tests/test_desactivation_utilisateur.py

DJANGO_SETTINGS_MODULE=config.settings.test pytest apps/accounts/tests/test_mots_de_passe_et_modification_profil.py \
  apps/accounts/tests/test_services_mots_de_passe.py

DJANGO_SETTINGS_MODULE=config.settings.test pytest apps/core/tests apps/accounts/tests/test_modele.py
```

### Vérifier Django sans pytest

```bash
python manage.py check --deploy
python manage.py test --settings=config.settings.test
```

Le chemin officiel du projet reste pytest-django pour les 24 fichiers de tests présents dans les applications.

## Qualité, sécurité et documentation

### Ruff

Ruff vérifie et trie les imports avec les règles du projet. Le formatage est vérifié sans modifier les fichiers :

```bash
ruff check .
ruff check --fix .
ruff format --check .
ruff format .
```

Pour vérifier uniquement les applications :

```bash
ruff check apps config
ruff format --check apps config
```

### Bandit

Analyse statique de sécurité :

```bash
bandit -c pyproject.toml -r apps config
```

Format JSON :

```bash
bandit -c pyproject.toml -f json -o bandit.json -r apps config
```

### Audit des dépendances

```bash
pip-audit -r requirements/dev.txt
pip-audit -r requirements/prod.txt
pip-audit --strict
```

### Schéma OpenAPI

Générer le schéma :

```bash
python manage.py spectacular --file docs/schema.yml --validate --fail-on-warn
```

Attention : le fichier versionné actuel est `docs/schema.yml`, mais certaines applications peuvent générer `docs/api/schema.yml`. Utilisez toujours le chemin réellement voulu par votre configuration ou votre CI.

Pour vérifier directement sans écrire de fichier :

```bash
python manage.py spectacular --validate --fail-on-warn
```

Si votre branche contient le dossier `docs/api/`, utilisez :

```bash
python manage.py spectacular --file docs/api/schema.yml --validate --fail-on-warn
```

### Référence JSON générée

Génération :

```bash
python manage.py generer_reference_json
```

Vérification :

```bash
python manage.py generer_reference_json --verifier
```

Cette commande vérifie ou génère `docs/api/REFERENCE_JSON_UTILISATEURS.md` selon son implémentation de gestion actuelle.

### Vérification globale de préparation CI

```bash
python manage.py check --database default
DJANGO_SETTINGS_MODULE=config.settings.test pytest
ruff check .
ruff format --check .
bandit -c pyproject.toml -r apps config
pip-audit -r requirements/dev.txt
python manage.py spectacular --file docs/schema.yml --validate --fail-on-warn
python manage.py generer_reference_json --verifier
```

## Déploiement en production

### Préparer `.env`

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.prod
SECRET_KEY=<clé Django longue et aléatoire>
JWT_CLE_SIGNATURE=<clé JWT longue, différente et aléatoire>
DEBUG=False
ALLOWED_HOSTS=api.exemple.fr,api.exemple.com
NOMBRE_PROXIES_DE_CONFIANCE=1

BASE_DE_DONNEES_URL=postgresql://stockflow_app:mot-de-passe@db-interne:5432/stockflow
BDD_TEST_UTILISATEUR=
BDD_TEST_MOT_DE_PASSE=

ACTIVER_DOCUMENTATION_API=False
CACHE_URL=rediscache://cache-interne:6379/1

EMAIL_HOST=smtp.exemple.fr
EMAIL_PORT=587
EMAIL_HOST_USER=stockflow
EMAIL_HOST_PASSWORD=<secret SMTP>
EMAIL_USE_TLS=True
EMAIL_FROM=StockFlow <noreply@exemple.fr>
URL_FRONTEND_REINITIALISATION=https://exemple.fr/reinitialiser-mot-de-passe
```

Les contrôles `prod.py` exigent :

- `ALLOWED_HOSTS` non vide ;
- `CACHE_URL` non vide ;
- `DEBUG=False` ;
- redirection HTTPS ;
- HSTS avec une durée d’un an ;
- cookies de session/CSRF sécurisés ;
- en-tête HTTPS derrière un proxy SSL.

Le schéma de cache Redis est donné à titre d’exemple. Vérifiez que votre dépendance/configuration Django fournit effectivement le backend Redis dans votre environnement. Sans backend Redis installé, utilisez un autre cache partagé pris en charge plutôt que `LocMemCache`.

### Vérifications pré-déploiement

```bash
python -m pip install -r requirements/prod.txt
python manage.py check --deploy --settings=config.settings.prod
python manage.py check --database default --settings=config.settings.prod
python manage.py makemigrations --check --dry-run --settings=config.settings.prod
python manage.py migrate --settings=config.settings.prod
python manage.py collectstatic --noinput --settings=config.settings.prod
```

### Collecte des fichiers statiques

La configuration utilise `STATIC_URL='static/'`, sans configuration de dossier `STATIC_ROOT`. Avant un déploiement servant les fichiers statiques via Django, ajoutez `STATIC_ROOT` dans les paramètres ou configurez votre proxy pour servir les fichiers collectés.

### Gunicorn

```bash
DJANGO_SETTINGS_MODULE=config.settings.prod gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --timeout 60 \
  --access-logfile - \
  --error-logfile - \
  config.wsgi:application
```

Gunicorn est défini dans `requirements/prod.txt`. Ne lancez pas plusieurs migrations simultanément sur la même base.

### Cache PostgreSQL partagé

Si aucun Redis n’est disponible, PostgreSQL peut héberger un cache avec le backend Django DatabaseCache :

```dotenv
CACHE_URL=dbcache://stockflow_cache
```

Puis :

```bash
python manage.py createcachetable --settings=config.settings.prod
python manage.py check --settings=config.settings.prod
```

Assurez-vous que `stockflow_cache` désigne une table Django existante dans la base choisie, selon la syntaxe de `django-environ` disponible dans votre environnement.

### Proxy HTTPS

Dans un déploiement derrière un reverse proxy, configurez :

- `X-Forwarded-Proto: https` côté proxy ;
- `NOMBRE_PROXIES_DE_CONFIANCE` avec le nombre réel de proxies de confiance ;
- les hôtes exacts dans `ALLOWED_HOSTS` ;
- TLS à la frontière du proxy ;
- HSTS uniquement après validation du HTTPS complet.

## Commandes utiles

```bash
# Shell Django
python manage.py shell

# Shell SQL interactif
python manage.py dbshell

# Interroger les migrations
python manage.py showmigrations
python manage.py makemigrations --dry-run --verbosity 3

# Charger l’état et les contraintes
python manage.py check --database default
python manage.py inspectdb

# Gestion des utilisateurs
python manage.py createsuperuser
python manage.py changepassword adresse@exemple.test

# Administration du cache
python manage.py createcachetable

# Nettoyage des sessions Django
python manage.py clearsessions

# Schéma OpenAPI
python manage.py spectacular --validate --fail-on-warn

# Référence JSON
python manage.py generer_reference_json
python manage.py generer_reference_json --verifier

# Tests
DJANGO_SETTINGS_MODULE=config.settings.test pytest
DJANGO_SETTINGS_MODULE=config.settings.test pytest -q
DJANGO_SETTINGS_MODULE=config.settings.test pytest -x
DJANGO_SETTINGS_MODULE=config.settings.test pytest --reuse-db
DJANGO_SETTINGS_MODULE=config.settings.test pytest --create-db
DJANGO_SETTINGS_MODULE=config.settings.test pytest --cov=apps --cov-report=term-missing

# Qualité
ruff check .
ruff format --check .
bandit -c pyproject.toml -r apps config
pip-audit -r requirements/dev.txt
```

## Dépannage

### `SECRET_KEY` non définie

Symptôme : Django échoue au démarrage avant les migrations.

Solution :

```bash
cp .env.example .env
python - <<'PY'
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
PY
```

Ajoutez la valeur à `.env`, puis générez séparément `JWT_CLE_SIGNATURE`.

### `JWT_CLE_SIGNATURE doit être distincte...`

Cause : les deux clés sont identiques ou la clé JWT contient moins de 50 caractères.

Solution :

```bash
python - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
```

Remplacez uniquement `JWT_CLE_SIGNATURE`, sans réutiliser `SECRET_KEY`.

### `django.db.utils.OperationalError`

Vérifiez d’abord :

```bash
pg_isready -h localhost -p 5432
psql -h localhost -U stockflow_app -d stockflow
python manage.py check --database default
```

- confirmez que PostgreSQL est démarré ;
- confirmez `BDD_HOTE`, `BDD_PORT`, `BDD_NOM` ;
- confirmez l’utilisateur, le mot de passe et les droits ;
- si `BASE_DE_DONNEES_URL` est définie, corrigez cette URL avant `BDD_*`.

### Django ne trouve pas la base temporaire des tests

Vérifiez :

```sql
ALTER ROLE stockflow_test CREATEDB;
\du stockflow_test
```

Puis :

```bash
DJANGO_SETTINGS_MODULE=config.settings.test pytest --create-db -vv
```

### `permission denied to create database`

L’utilisateur `BDD_TEST_UTILISATEUR` n’a pas `CREATEDB` :

```sql
ALTER ROLE stockflow_test CREATEDB;
```

Ne lancez pas les tests avec `stockflow_app` si ce rôle n’a pas explicitement besoin de créer des bases temporaires.

### `ALLOWED_HOSTS doit être configuré en production`

Ajoutez au `.env` de production :

```dotenv
ALLOWED_HOSTS=api.exemple.fr
```

Pour plusieurs hôtes :

```dotenv
ALLOWED_HOSTS=api.exemple.fr,api.exemple.com
```

### `CACHE_URL doit désigner un cache partagé en production`

Ajoutez un cache réellement disponible : Redis, Memcached ou DatabaseCache, selon votre infrastructure.

### Les e-mails ne sont pas envoyés en développement

C’est normal : `dev.py` utilise `django.core.mail.backends.console.EmailBackend`. Les e-mails sont affichés dans le terminal plutôt que transmis via SMTP.

### Swagger inaccessible

En développement :

```dotenv
ACTIVER_DOCUMENTATION_API=True
```

Puis :

```bash
python manage.py runserver
```

Ouvrez `http://127.0.0.1:8000/api/v1/docs/`.

### Port 8000 déjà utilisé

```bash
python manage.py runserver 127.0.0.1:8080
```

### Le serveur affiche des erreurs HTTPS ou HSTS en local

Ne chargez pas `config.settings.prod` pour les tests locaux si les certificats HTTPS ne sont pas configurés. Utilisez `config.settings.dev` :

```bash
python manage.py runserver --settings=config.settings.dev
```

### Nettoyage d’un environnement virtuel cassé

```bash
deactivate 2>/dev/null || true
rm -rf .venv
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/dev.txt
```

Sous Windows PowerShell :

```powershell
deactivate
Remove-Item -Recurse -Force .venv
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements/dev.txt
```

## Sécurité opérationnelle

- Ne jamais committer `.env`, les clés JWT ou les mots de passe PostgreSQL.
- Utiliser deux bases distinctes : application et test.
- Ne jamais donner `SUPERUSER` au compte applicatif Django.
- Utiliser `CREATEDB` uniquement pour le rôle PostgreSQL des tests.
- Utiliser HTTPS en production.
- Désactiver Swagger en production sauf nécessité explicite.
- Sauvegarder la base avant toute migration.
- Faire tourner les tests avant chaque déploiement.
- Réguler les secrets via un gestionnaire de secrets en production.
- Utiliser des mots de passe de base de données aléatoires, longs et différents par environnement.
- Changer régulièrement `SECRET_KEY`/`JWT_CLE_SIGNATURE` uniquement avec un plan de rotation : elles invalident les sessions ou jetons concernés selon leur rôle.
