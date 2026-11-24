# Déploiement FlowStock sur un VPS Linux

Cette configuration déploie uniquement l’API Django et PostgreSQL avec Docker Compose. Elle ne choisit ni ne provisionne de fournisseur VPS, domaine, pare-feu, sauvegarde ou proxy HTTPS. Le client Expo reste livré séparément.

## Pré-requis

- Un VPS Linux choisi par l’équipe, joignable en SSH, avec Docker Engine et le plugin Compose v2 installés. Vérifiez que l’offre gratuite autorise Docker et fournit assez de mémoire, de stockage persistant et une architecture prise en charge (`linux/amd64` ou `linux/arm64`).
- Un utilisateur Linux dédié au déploiement, accès SSH par clé et droits Docker. L’accès au socket Docker équivaut pratiquement à des droits root : protégez cette clé et limitez les personnes qui peuvent publier des tags `v*`.
- Un domaine pointant vers le VPS et un proxy inverse HTTPS installé sur l’hôte (par exemple Caddy ou Nginx). Le proxy doit transmettre `Host` et `X-Forwarded-Proto: https` vers `127.0.0.1:8000` (ou le port choisi). N’exposez publiquement que SSH et les ports HTTPS/HTTP nécessaires au proxy; ne configurez pas de publication de port pour PostgreSQL.
- Le package backend `ghcr.io/<propriétaire>/<dépôt>-api` accessible au `GITHUB_TOKEN` du dépôt avec le droit `packages: read`. Le workflow transmet ce jeton temporairement par le canal SSH chiffré, l’utilise avec `docker login --password-stdin`, puis supprime le répertoire Docker temporaire. Aucun PAT GHCR permanent ni secret de registre supplémentaire n’est requis. Si le package n’accorde pas automatiquement l’accès au dépôt, ajoutez ce dépôt dans les paramètres d’accès du package.

## Secrets et variable GitHub Actions

Ajoutez ces **Actions repository secrets** (ou secrets d’environnement si le workflow est adapté pour cibler cet environnement) :

| Secret                | Valeur                                                                                                                                                                |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VPS_HOST`            | Adresse IPv4 ou nom DNS du VPS, sans `user@` ni port.                                                                                                                 |
| `VPS_USER`            | Nom de l’utilisateur Linux dédié, différent de `root`.                                                                                                                |
| `VPS_SSH_PORT`        | Port SSH numérique du serveur (souvent `22`).                                                                                                                         |
| `VPS_SSH_PRIVATE_KEY` | Clé privée dédiée acceptée par cet utilisateur; ne la commitez jamais.                                                                                                |
| `VPS_SSH_KNOWN_HOSTS` | Ligne `known_hosts` pour cet hôte/port, dont l’empreinte a été vérifiée par un canal indépendant. N’utilisez pas aveuglément `ssh-keyscan` pour établir la confiance. |
| `VPS_DEPLOY_PATH`     | Répertoire absolu appartenant à l’utilisateur, par exemple `/opt/flowstock`. Le workflow y téléverse `compose.yml`; le fichier `.env` doit déjà s’y trouver.          |

Ajoutez la **repository variable** `VPS_DEPLOY_ENABLED` avec la valeur `true` uniquement une fois le VPS, le fichier `.env`, les secrets et l’accès GHCR prêts. La variable sert de verrou explicite; lorsqu’elle est absente ou différente, le job de déploiement est ignoré.

Le `GITHUB_TOKEN` est fourni automatiquement par Actions avec `packages: read` dans le job de déploiement; ne créez pas de secret GHCR supplémentaire. Le jeton est utilisé uniquement pour le pull de cette livraison et n’est pas conservé dans le `.env` ni dans la configuration Docker persistante du serveur.

Le dépôt ne reçoit pas les secrets de production. Les pull requests exécutent les contrôles sans secrets et ne déploient jamais. Les secrets SSH ne sont utilisés que par le job dépendant de la publication d’une image sur un push de tag `v*`.

## Préparer le serveur

1. Installer et tester Docker Engine ainsi que `docker compose version` avec l’utilisateur de déploiement. Garder l’accès SSH initial d’administration distinct de la clé de déploiement.
2. Installer le proxy inverse sur l’hôte, configurer TLS/certificat et acheminer le domaine vers le port loopback choisi. La configuration Django active les redirections HTTPS en production; le proxy doit donc transmettre l’en-tête HTTPS attendu. Gardez le port PostgreSQL fermé et non publié.
3. Créer le répertoire de déploiement et le `.env` sur le serveur. Copiez le contenu de [`.env.example`](.env.example), puis retirez le suffixe `.example` : le workflow ne téléverse jamais ce modèle.
4. Générez les secrets sur le VPS ou une machine d’administration sécurisée, puis saisissez-les directement dans le fichier `.env` avec des permissions strictes. Pour éviter les problèmes d’encodage de l’URL PostgreSQL construite par Compose, utilisez pour le mot de passe PostgreSQL une valeur hexadécimale, sans caractères réservés d’URL. Utilisez une clé secrète Django longue et aléatoire.
5. Remplacez `FLOWSTOCK_IMAGE` dans le `.env` par le vrai nom du package et un tag initial existant, le domaine d’exemple dans `ALLOWED_HOSTS` par le domaine réel, puis vérifiez que `DJANGO_DEBUG=False` et `SECURE_SSL_REDIRECT=True`. Gardez les origines CORS vides si aucun client web sur une autre origine n’en a besoin; si elles sont renseignées, configurez aussi exactement `CSRF_TRUSTED_ORIGINS`.
6. Limitez les permissions du fichier : `chmod 600 .env`. N’envoyez jamais son contenu dans GitHub Actions, dans un ticket ou dans les journaux.
7. Vérifiez que le dépôt GitHub a accès au package GHCR, puis configurez les secrets et la variable GitHub décrits ci-dessus. Vérifiez également les règles de protection des tags/release avant d’autoriser le job automatique.

## Déploiement et comportement

Poussez un tag de version `v*` après validation. Le workflow existant exécute d’abord les contrôles backend et mobile, puis construit et publie l’image backend multi-architecture. Si `VPS_DEPLOY_ENABLED=true`, le job suivant vérifie l’hôte SSH avec `known_hosts`, copie atomiquement le Compose, valide la configuration, tire l’image du tag publié, attend PostgreSQL, applique les migrations et fichiers statiques, puis attend que l’API soit saine sur `/healthz/`.

Les données PostgreSQL, les médias et les fichiers statiques utilisent des volumes Docker persistants. Le port API est lié par défaut à `127.0.0.1:8000`; le port PostgreSQL n’est pas publié. Le proxy inverse fourni et configuré par l’opérateur reste responsable du HTTPS et de l’exposition publique.

Pour inspecter le service après un déploiement, connectez-vous au serveur et utilisez les commandes Docker Compose depuis le répertoire de déploiement, par exemple `docker compose ps` et `docker compose logs api`. Avant toute migration destructive, prenez une sauvegarde testée de la base. Cette configuration ne met pas en place de sauvegardes, restauration, supervision, mises à jour du système, rotation des secrets ni retour automatique à la version précédente.

## Ce qui n’est pas encore raccordé

Aucun fournisseur ou hôte VPS n’a été choisi ni configuré dans le cadre de ce changement. L’adresse, l’utilisateur, la clé et l’empreinte SSH, les règles réseau, le domaine, TLS, les identifiants locaux de base et le fichier `.env` doivent donc être fournis/configurés avant la première livraison. Aucun déploiement réel n’est revendiqué. Si le VPS gratuit ne permet pas Docker/Compose ou manque de ressources, il faudra choisir une autre offre ou une cible différente.
