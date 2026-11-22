-- Gestion de stock pour commerçant en ligne - 3FN
-- Syntaxe PostgreSQL (adaptable MySQL / SQLite)

CREATE TABLE Categorie (
    idCategorie   SERIAL PRIMARY KEY,
    nomCategorie  VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE Fournisseur (
    idFournisseur   SERIAL PRIMARY KEY,
    nomFournisseur  VARCHAR(120) NOT NULL
);

CREATE TABLE Utilisateur (
    idUser      SERIAL PRIMARY KEY,
    nomUser     VARCHAR(100) NOT NULL,
    email       VARCHAR(120) NOT NULL UNIQUE,
    motDePasse  VARCHAR(255) NOT NULL,              -- toujours hashé (bcrypt, argon2...)
    role        VARCHAR(15) NOT NULL DEFAULT 'vendeur'
                CHECK (role IN ('admin','vendeur'))
);

CREATE TABLE Produit (
    idProduit      SERIAL PRIMARY KEY,
    nomProduit     VARCHAR(150) NOT NULL,
    prixVente      NUMERIC(12,2) NOT NULL CHECK (prixVente >= 0),
    prixAchat      NUMERIC(12,2) NOT NULL CHECK (prixAchat >= 0),
    seuilAlerte    INT NOT NULL DEFAULT 0,
    photo          VARCHAR(255),                -- chemin ou URL de l'image (le fichier est stocké hors base)
    isActif        BOOLEAN NOT NULL DEFAULT TRUE,
    idCategorie    INT REFERENCES Categorie(idCategorie),
    idFournisseur  INT REFERENCES Fournisseur(idFournisseur)
);

CREATE TABLE Client (
    idClient   SERIAL PRIMARY KEY,
    nomClient  VARCHAR(120) NOT NULL,
    contact    VARCHAR(120),
    adresse    VARCHAR(255)
);

CREATE TABLE Commande (
    idCommande  SERIAL PRIMARY KEY,
    idClient    INT NOT NULL REFERENCES Client(idClient),
    idUser      INT NOT NULL REFERENCES Utilisateur(idUser),
    date        DATE NOT NULL DEFAULT CURRENT_DATE,
    statut      VARCHAR(15) NOT NULL DEFAULT 'en_attente'
                CHECK (statut IN ('en_attente','confirmee','annulee'))
);

CREATE TABLE LigneCommande (
    idLigne       SERIAL PRIMARY KEY,
    idCommande    INT NOT NULL REFERENCES Commande(idCommande) ON DELETE CASCADE,
    idProduit     INT NOT NULL REFERENCES Produit(idProduit),
    quantite      INT NOT NULL CHECK (quantite > 0),
    prixUnitaire  NUMERIC(12,2) NOT NULL,   -- prix de vente au moment de la commande
    coutUnitaire  NUMERIC(12,2) NOT NULL,   -- prix d'achat au moment de la commande
    UNIQUE (idCommande, idProduit)
);

CREATE TABLE Livraison (
    idLivraison    SERIAL PRIMARY KEY,
    idCommande     INT NOT NULL UNIQUE REFERENCES Commande(idCommande),
    dateLivraison  DATE,
    statut         VARCHAR(15) NOT NULL DEFAULT 'en_cours'
                   CHECK (statut IN ('en_cours','livree','echec')),
    cout           NUMERIC(12,2) NOT NULL DEFAULT 0,  -- coût supporté par le commerçant
    fraisFacture   NUMERIC(12,2) NOT NULL DEFAULT 0   -- payé par le client
);

CREATE TABLE Mouvement (
    idMouvement    SERIAL PRIMARY KEY,
    idProduit      INT NOT NULL REFERENCES Produit(idProduit),
    typeMouvement  VARCHAR(10) NOT NULL
                   CHECK (typeMouvement IN ('entree','sortie','perte')),
    quantite       INT NOT NULL CHECK (quantite > 0),  -- toujours positive, le type donne le sens
    date           DATE NOT NULL DEFAULT CURRENT_DATE,
    idUser         INT NOT NULL REFERENCES Utilisateur(idUser),
    idCommande     INT REFERENCES Commande(idCommande) -- rempli pour les sorties liées à une commande
);

-- Pour le bénéfice net (facultative)
CREATE TABLE Depense (
    idDepense  SERIAL PRIMARY KEY,
    date       DATE NOT NULL DEFAULT CURRENT_DATE,
    libelle    VARCHAR(150) NOT NULL,
    montant    NUMERIC(12,2) NOT NULL CHECK (montant >= 0)
);

CREATE INDEX idx_mouvement_produit ON Mouvement(idProduit);
CREATE INDEX idx_ligne_produit     ON LigneCommande(idProduit);
CREATE INDEX idx_livraison_date    ON Livraison(dateLivraison);

-- ======================================================================
-- VUES
-- ======================================================================

-- Stock actuel = entrées - sorties - pertes
CREATE VIEW v_stock AS
SELECT p.idProduit, p.nomProduit, p.seuilAlerte,
       COALESCE(SUM(CASE m.typeMouvement WHEN 'entree' THEN m.quantite
                                         ELSE -m.quantite END), 0) AS stock_actuel
FROM Produit p
LEFT JOIN Mouvement m ON m.idProduit = p.idProduit
GROUP BY p.idProduit, p.nomProduit, p.seuilAlerte;

CREATE VIEW v_alerte_stock AS
SELECT * FROM v_stock WHERE stock_actuel <= seuilAlerte;

-- Produits avec leur fournisseur
CREATE VIEW v_produit_fournisseur AS
SELECT p.idProduit, p.nomProduit, f.idFournisseur, f.nomFournisseur
FROM Produit p
LEFT JOIN Fournisseur f ON f.idFournisseur = p.idFournisseur;

-- Bénéfice par commande livrée = marge produits + frais facturés - coût de livraison
CREATE VIEW v_benefice_commande AS
SELECT c.idCommande, l.dateLivraison,
       SUM(lc.quantite * lc.prixUnitaire) + l.fraisFacture AS chiffre_affaires,
       SUM(lc.quantite * (lc.prixUnitaire - lc.coutUnitaire))
         + l.fraisFacture - l.cout                          AS benefice
FROM Commande c
JOIN Livraison l      ON l.idCommande = c.idCommande AND l.statut = 'livree'
JOIN LigneCommande lc ON lc.idCommande = c.idCommande
WHERE c.statut <> 'annulee'
GROUP BY c.idCommande, l.dateLivraison, l.fraisFacture, l.cout;

-- Bénéfice par produit (commandes livrées)
CREATE VIEW v_benefice_produit AS
SELECT p.idProduit, p.nomProduit,
       SUM(lc.quantite)                                          AS qte_vendue,
       SUM(lc.quantite * lc.prixUnitaire)                        AS chiffre_affaires,
       SUM(lc.quantite * (lc.prixUnitaire - lc.coutUnitaire))    AS benefice_brut
FROM LigneCommande lc
JOIN Commande c  ON c.idCommande = lc.idCommande AND c.statut <> 'annulee'
JOIN Livraison l ON l.idCommande = c.idCommande AND l.statut = 'livree'
JOIN Produit p   ON p.idProduit = lc.idProduit
GROUP BY p.idProduit, p.nomProduit;

-- Bénéfice net mensuel = bénéfice des commandes livrées - dépenses
CREATE VIEW v_benefice_mensuel AS
SELECT m.mois,
       COALESCE(b.benefice, 0) AS benefice_brut,
       COALESCE(d.total, 0)    AS depenses,
       COALESCE(b.benefice, 0) - COALESCE(d.total, 0) AS benefice_net
FROM (SELECT DISTINCT date_trunc('month', dateLivraison)::date AS mois
      FROM v_benefice_commande
      UNION
      SELECT DISTINCT date_trunc('month', date)::date FROM Depense) m
LEFT JOIN (SELECT date_trunc('month', dateLivraison)::date AS mois, SUM(benefice) AS benefice
           FROM v_benefice_commande GROUP BY 1) b ON b.mois = m.mois
LEFT JOIN (SELECT date_trunc('month', date)::date AS mois, SUM(montant) AS total
           FROM Depense GROUP BY 1) d ON d.mois = m.mois
ORDER BY m.mois;
