# FlowStock

Application de gestion de stock avec une API Django hébergée sur Render et une
application Expo installée sur téléphone. L’app mobile appelle directement l’API.

## Déployer sur Render

[![Déployer sur Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Panda0831/DEP_FLOWSTOCK)

Le Blueprint crée l’API Docker et PostgreSQL. Configurez l’URL de cette API dans
l’application Expo avant de la lancer ou de la compiler pour le téléphone.
Consultez
[`deploy/render/README.md`](deploy/render/README.md) pour les limites du plan
gratuit et les étapes après le déploiement.
