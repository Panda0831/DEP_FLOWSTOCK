# Résumé — Pipeline CI/CD VPS FlowStock

## Prêt dans le dépôt

- Le workflow existant conserve les tests Django/Expo et la publication GHCR multi-architecture uniquement pour les tags `v*`. Un job `deploy-vps` attend la fin de la publication, ne s’exécute que sur un push de tag `v*` et nécessite la variable de dépôt `VPS_DEPLOY_ENABLED=true`. Les PR et `workflow_dispatch` ne déploient pas; les jobs CI n’utilisent pas les secrets VPS.
- Le déploiement utilise SSH natif avec clé privée et `known_hosts` vérifié, valide les paramètres, téléverse le Compose, tire le tag publié, attend PostgreSQL, exécute migrations et `collectstatic`, puis attend l’état sain `/healthz/`.
- L’accès GHCR utilise le `GITHUB_TOKEN` du job, limité à `packages: read`, envoyé par stdin via SSH; Docker emploie un répertoire de configuration temporaire supprimé à la fin. Aucun PAT de registre n’est conservé sur le VPS.
- `deploy/vps/compose.yml` fournit API et PostgreSQL, avec stockage persistant. PostgreSQL n’a aucun port publié; l’API est liée à `127.0.0.1` pour être placée derrière un proxy HTTPS sur l’hôte.
- `deploy/vps/.env.example` ne contient que des valeurs d’exemple. La procédure des secrets GitHub, du `.env`, du serveur, de GHCR, du domaine/proxy TLS et des limites opérationnelles est dans `deploy/vps/README.md`; le README backend renvoie vers cette procédure.

## Vérifications effectuées

- Diagnostics statiques VS Code : aucune erreur dans le workflow, Compose, l’exemple `.env` et les documentations.
- `docker compose config --quiet` : réussi avec des valeurs factices; aucun déploiement ni accès réseau n’a été tenté.
- Syntaxe Bash des trois blocs `run` multilignes : valide; conditions de tag et dépendance au job de publication vérifiées.
- Django `check` et `makemigrations --check --dry-run` : réussis dans l’environnement virtuel local (avec avertissements de préfixe Python déjà présents dans cet environnement).
- Ruff et les tests Django complets n’ont pas pu être validés localement : Ruff et pytest ne sont pas installés dans le virtualenv; pytest système ne peut pas collecter les tests, notamment à cause de dépendances manquantes (`django-environ`, `openpyxl`).
- ESLint mobile : réussi avec un avertissement de dépendance de hook dans un fichier Expo déjà modifié dans l’espace de travail. TypeScript échoue sur `Frontend/mobile/src/app/stock/new.tsx` : le type `Produit` ne définit pas la propriété `stock`. Ce fichier fait partie des modifications locales préexistantes et n’a pas été modifié dans cette tâche; l’état de travail actuel bloque donc le job mobile, puis la publication/déploiement, tant que l’erreur n’est pas corrigée.

## À fournir/configurer avant le premier déploiement

- Choisir et provisionner un VPS Linux gratuit compatible Docker Engine/Compose et l’image amd64/arm64; fournir l’adresse, utilisateur non-root, port SSH et accès initial sécurisé.
- Configurer le proxy inverse HTTPS, domaine/certificat, pare-feu, sauvegardes et accès GHCR du dépôt au `GITHUB_TOKEN`.
- Créer sur le VPS le fichier `.env` de production à partir de `deploy/vps/.env.example`, avec secrets générés localement, domaine dans `ALLOWED_HOSTS`, paramètres PostgreSQL et permissions `600`.
- Configurer les secrets Actions `VPS_HOST`, `VPS_USER`, `VPS_SSH_PORT`, `VPS_SSH_PRIVATE_KEY`, `VPS_SSH_KNOWN_HOSTS`, `VPS_DEPLOY_PATH`, puis mettre `VPS_DEPLOY_ENABLED=true` après vérification des accès et protections de tags.

Aucun hôte, secret ou accès VPS n’a été fourni. Aucun déploiement réel n’a été exécuté ou revendiqué.

## Versionnement

La branche `modernize/python-20261124192802` a été créée. Aucun commit n’a été effectué : l’espace de travail contenait déjà des modifications non liées (documentation API, code/tests backend et écrans Expo), et l’opération de commit disponible inclut tous les changements. Ils ont été laissés intacts pour éviter de les inclure dans ce changement de déploiement.
