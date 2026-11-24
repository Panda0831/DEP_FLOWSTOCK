# TODO FlowStock

## Terminé sur `Front_Eric`

- [x] Intégrer le dernier push de `origin/Front_Eric` (`a35577c`, fast-forward).
- [x] Gérer les achats fournisseur avec référence, lignes, statut de réception et solde à payer.
- [x] Autoriser la modification d’un achat uniquement avant sa première réception ou son premier paiement, avec historique des actions.
- [x] Gérer les réceptions partielles sans augmenter le stock avant la réception; refuser les quantités supérieures au reste à recevoir.
- [x] Gérer les retours fournisseur sans dépasser les quantités reçues ni rendre le stock négatif; tracer motif et référence d’achat.
- [x] Enregistrer des paiements partiels fournisseur et client, avec mode, date, solde et historique.
- [x] Gérer les commandes avec remise, frais de livraison, confirmation, annulation et protection contre un stock négatif.
- [x] Gérer la préparation, l’expédition, la livraison, l’échec, la reprise et le retour client; les retours réintègrent le stock.
- [x] Mettre à jour les écrans mobiles Achats, Commandes et Livraisons ainsi que la documentation API.
- [x] Vérifier : 21 tests backend réussis, `manage.py check`, migrations synchronisées, Ruff, lint mobile, TypeScript et `git diff --check`.

## À faire ensuite

- [ ] Ajouter une recherche et des filtres simples dans les listes des livraisons et des achats (client/fournisseur, article, statut).
- [ ] Remplacer la saisie manuelle des dates des rapports par des périodes prédéfinies (« Ce mois », « Mois dernier ») et un choix de dates personnalisé.
- [ ] Permettre de lancer un réapprovisionnement directement depuis une alerte de stock, avec le produit déjà sélectionné.
- [ ] Améliorer la lisibilité mobile : augmenter les textes secondaires trop petits et vérifier le contraste et l’affichage avec une grande taille de texte.
- [ ] Afficher un message clair et une marche à suivre quand une connexion est temporairement bloquée après plusieurs échecs.
- [x] Ajouter une CI GitHub Actions : contrôles Django, migrations, tests, Ruff, ESLint et TypeScript sur push et pull request.
- [x] Ajouter la construction de l’image Docker backend à la CI; publier les images multi-architecture dans GHCR sur les tags `v*`.
- [ ] Raccorder le déploiement automatique au VPS après choix de l’hébergeur et ajout de la configuration/secrets.
- [ ] Choisir le canal de distribution de l’application Expo (EAS Build ou autre) et ses identifiants de signature.
- [ ] Ajouter les ajustements manuels positifs et négatifs de stock avec motif obligatoire, date, utilisateur et référence d’opération, conformément au cahier des charges.
- [ ] Vérifier le déploiement des migrations sur la base MySQL cible et faire un parcours d’acceptation sur mobile avec des données représentatives.
- [ ] Confirmer que les achats retournés au fournisseur et les remboursements éventuels sont traités comme attendu par les règles comptables du projet.

## Plus tard — rapports

- [ ] Reprendre les rapports PDF (financier, ventes, achats, dépenses, mouvements de stock et activité globale), leurs filtres de période et leur export/partage.

## État Git

- Branche : `Front_Eric`; `HEAD` et `origin/Front_Eric` étaient tous deux sur `a35577c` à la dernière vérification.
- Les changements locaux ne sont pas commités ni poussés.
- Le stash de récupération `avant merge Front_Eric a35577c` est conservé.
