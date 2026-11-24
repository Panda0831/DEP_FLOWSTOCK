# Plan de finalisation CI/CD — FlowStock

## Objectif et périmètre

Compléter le workflow GitHub Actions existant pour déployer le backend Django de FlowStock sur un VPS Linux compatible Docker Compose, uniquement après la réussite des contrôles CI et la publication de l’image GHCR d’un tag `v*`. Les vérifications pull request restent sans secrets et sans déploiement. Aucun déploiement réel ne sera lancé pendant cette tâche : aucun hôte ni accès VPS n’a été fourni.

Le dépôt contient déjà `Bakend/Dockerfile`, une image publiée sous `ghcr.io/<propriétaire>/<dépôt>-api` sur les tags de version et l’endpoint `/healthz/`. Il ne contient pas encore de stack Compose VPS. Le frontend Expo est contrôlé par la CI, mais n’est pas une unité de déploiement VPS dans ce périmètre.

## Décisions de sécurité

- Conserver les jobs de tests backend/mobile sans secrets; le job de publication d’image demeure limité aux tags `v*`.
- Ajouter un job de déploiement dépendant de la publication d’image, limité à un push de tag `v*`, avec activation explicite par la variable de dépôt `VPS_DEPLOY_ENABLED=true`. Les pull requests et `workflow_dispatch` ne déploient jamais.
- Utiliser OpenSSH fourni par le runner GitHub, une clé privée enregistrée dans GitHub Secrets et une empreinte `known_hosts` pré-vérifiée. Ne pas désactiver la vérification d’hôte ni utiliser `ssh-keyscan` comme source de confiance.
- Garder la configuration de production et les secrets applicatifs uniquement dans le fichier `.env` créé directement sur le VPS, jamais dans le dépôt ou les artefacts du workflow.
- Accorder `packages: read` uniquement au job de déploiement et transmettre son `GITHUB_TOKEN` au VPS par stdin SSH chiffré. Utiliser un `DOCKER_CONFIG` temporaire supprimé à la fin du déploiement pour éviter tout PAT GHCR permanent ou identifiant de registre persistant.
- Ne publier aucun port PostgreSQL. N’exposer l’API que sur `127.0.0.1` du VPS, derrière un proxy inverse HTTPS configuré séparément.
- Faire persister les données PostgreSQL et les médias dans des volumes Docker; faire attendre la base avant les migrations et le démarrage de l’API.

## Fichiers visés

1. Modifier `.github/workflows/ci.yml` : ajouter le job de déploiement SSH protégé par les conditions décrites ci-dessus, publier le tag exact du backend et exécuter les migrations avant la mise en service.
2. Créer `deploy/vps/compose.yml` : services API/PostgreSQL, contrôle `/healthz/`, volumes persistants, base non publiée et port API lié à l’interface loopback uniquement.
3. Créer `deploy/vps/.env.example` : modèle sans valeurs secrètes réelles pour la configuration serveur.
4. Créer `deploy/vps/README.md` : prérequis Linux/VPS, accès GHCR du dépôt, préparation du compte/clé/empreinte SSH, secrets et variable GitHub, création du `.env`, proxy HTTPS, activation et limites opérationnelles.
5. Modifier `Bakend/README.md` : remplacer la note indiquant qu’aucun déploiement VPS n’est raccordé par un renvoi vers la procédure générique.

## Étapes d’exécution

1. Enregistrer ce plan et le suivi initial, puis consulter le plan comme source de vérité.
2. Préparer une branche via la politique de contrôle de version requise par l’environnement, sans commandes Git directes.
3. Créer les fichiers Compose et le guide de mise en service; modifier le workflow et le README backend, sans modifier le code applicatif.
4. Vérifier statiquement le YAML du workflow et de Compose, les conditions d’événement, l’absence de secrets en clair, l’absence de port PostgreSQL publié et l’utilisation de l’image publiée attendue.
5. Exécuter les validations locales adaptées disponibles (lint YAML si installé, vérification Compose si Docker Compose est disponible, tests CI existants si l’environnement le permet). Aucun déploiement, accès distant, création d’hôte ou rotation de secrets ne sera simulé ni revendiqué.
6. Mettre à jour `progress.md`, rédiger `summary.md` avec les résultats et les prérequis encore à fournir, puis enregistrer les changements sur la branche selon la politique de versionnement.

## Données/infra qui restent à fournir par l’utilisateur

- Un VPS Linux gratuit choisi et joignable, DNS/domaine éventuel, ressources et architecture CPU compatibles avec l’image multi-architecture.
- Accès administrateur initial pour installer Docker Engine et le plugin Compose, créer un utilisateur de déploiement et configurer pare-feu, sauvegardes et proxy inverse TLS.
- Secrets GitHub `VPS_HOST`, `VPS_USER`, `VPS_SSH_PRIVATE_KEY`, `VPS_SSH_KNOWN_HOSTS`, `VPS_DEPLOY_PATH` et `VPS_SSH_PORT`; variable de dépôt `VPS_DEPLOY_ENABLED=true` seulement après configuration.
- Accès du dépôt GitHub au package GHCR pour que le `GITHUB_TOKEN` du workflow puisse le tirer.
- Fichier `.env` de production créé manuellement dans le répertoire de déploiement du VPS, avec secrets générés localement et valeurs de domaine/base conformes au modèle.
