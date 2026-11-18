# Guide du back-office Boxing Shop

Ce guide s'adresse à l'équipe de la boutique : aucune connaissance technique n'est nécessaire.

**Adresse** : `https://votre-domaine/admin/` — connectez-vous avec votre e-mail et votre mot de passe.
Le lien « Voir la boutique ↗ », en haut à droite, ouvre le site dans un nouvel onglet.

---

## 1. Le tableau de bord

La page d'accueil du back-office affiche quatre compteurs, cliquables :

| Compteur | Ce qu'il signifie | Action |
|---|---|---|
| **Commandes à préparer / expédier** | Commandes payées pas encore expédiées | Préparer les colis (voir §3) |
| **SKU sous le seuil critique** (rouge) | Déclinaisons dont le stock est inférieur ou égal au seuil d'alerte | Réapprovisionner (voir §2.3) |
| **Demandes Club / Coach** | Clubs en attente de validation | Valider ou refuser (voir §5) |
| **CA TTC 30 jours** | Chiffre d'affaires encaissé sur 30 jours | Ouvre l'export comptable |

Sous les compteurs, le tableau **Alertes stock** liste les 25 déclinaisons les plus critiques
(« RUPTURE » = stock à zéro). Un message rouge signale les commandes annulées automatiquement parce qu'un
article s'est retrouvé épuisé au moment du paiement : le client a été **remboursé et prévenu automatiquement**.

Un e-mail d'alerte est aussi envoyé à l'adresse de l'administrateur dès qu'une vente fait passer un article sous son seuil.

---

## 2. Le catalogue

### 2.1 Vocabulaire

- **Discipline** : Boxe anglaise, Muay Thaï & Kickboxing, MMA & Grappling, JJB, Entraînement & Sacs.
- **Type** : Gants, Protections, Tenues, Bandages & Soins, Matériel de club (sous-types possibles).
- **Produit** : la fiche (nom, description, caractéristiques, photos).
- **Déclinaison (SKU)** : une combinaison vendable couleur / poids (oz) / taille, avec **son prix et son stock**.
  Exemple : « Gant Heritage — Noir / 14 oz » est une déclinaison du produit « Gant Heritage ».

### 2.2 Créer ou modifier un produit

*Catalogue → Produits → Ajouter un produit* (ou cliquer sur un produit existant).

1. **Informations** : nom (l'adresse web se remplit seule), discipline principale, disciplines compatibles, type,
   accroche (1 phrase, visible dans les listes), description.
   Dans la description : laissez une ligne vide entre deux paragraphes, commencez une ligne par `## ` pour un
   intertitre et par `- ` pour une puce.
2. **Caractéristiques** : matière, niveau, gamme, rembourrage, fermeture, origine. *Spécifications
   complémentaires* accepte des paires libres, par exemple `{"Poids unitaire": "380 g", "Lavage": "30 °C"}`.
3. **Tableau de tailles** : laissez vide pour utiliser celui du type de produit.
4. **Photos** (en bas) : téléversez une image (JPEG/PNG, idéalement carrée, 1 400 px ou plus) et renseignez le
   **texte alternatif** (description courte pour les personnes malvoyantes et Google). Le site crée
   automatiquement les versions WebP optimisées. La première photo (ordre le plus petit) est la photo principale.
5. **Déclinaisons** (en bas) : une ligne par combinaison. SKU unique (ex. `BS-GHC-NOI-14`), couleur + code
   couleur (`#0D0D0D`), poids en oz *ou* taille, prix TTC, **prix barré** si promotion, stock, seuil d'alerte.
6. **SEO** (section repliable) : titre (≈ 60 caractères) et description (≈ 155 caractères) affichés par Google.
   Vides = générés automatiquement à partir du nom et de l'accroche.
7. Décochez **En ligne** pour masquer un produit sans le supprimer (conseillé : on garde l'historique).

### 2.3 Mettre à jour les stocks

*Catalogue → Déclinaisons (SKU)* : la colonne **stock** est modifiable directement dans la liste ; cliquez sur
**Enregistrer** en bas. Filtre à droite **alerte stock → Sous le seuil critique** pour ne voir que les urgences.
Le stock baisse automatiquement à chaque paiement confirmé ; il n'est **pas** réservé tant que le client n'a pas payé.

### 2.4 Guides, avis, tableaux de tailles

- *Contenus éditoriaux → Guides techniques* : article (même mise en forme que les descriptions), produits et types liés. Les produits
  liés affichent le guide sur leur fiche, et le guide affiche les produits.
- *Catalogue → Avis clients* : les avis clients arrivent **non publiés**. Relisez-les puis cochez **publié**
  (ou utilisez l'action groupée). Un avis publié alimente la note moyenne affichée sur Google.
- *Catalogue → Tableaux de tailles* : lignes taille / poids / tour de main / hauteur, utilisées sur les fiches.

---

## 3. Les commandes

*Commandes & factures → Commandes*. Filtres à droite (statut, date), recherche par n° de commande, e-mail, nom, n° de suivi ou SKU.

### Statuts

| Statut | Signification | Qui le change |
|---|---|---|
| En attente de paiement | Client parti payer sur Stripe | Automatique |
| **Payée** | Paiement confirmé, stock décrémenté, facture créée, e-mail envoyé | Automatique |
| En préparation | Colis en cours | Vous |
| **Expédiée** | Colis remis au transporteur | Vous (n° de suivi obligatoire) |
| Livrée | Colis reçu | Vous |
| Annulée | Paiement abandonné, ou rupture au paiement (remboursé) | Automatique ou vous |

### Expédier une commande

1. Ouvrez la commande, vérifiez les articles (SKU) et l'adresse.
2. Statut **Expédiée**, renseignez le **transporteur**, le **n° de suivi** et si possible le **lien de suivi**.
3. Enregistrez : le client reçoit **automatiquement** un e-mail avec son suivi, et la date d'expédition est notée.

Actions groupées (cocher plusieurs commandes, menu « Action ») : *Passer en préparation*, *Marquer comme livrées*,
*Exporter la sélection (CSV)*.

Les commandes ne peuvent pas être supprimées (ce sont des pièces comptables) ; une commande non payée ne peut
pas être expédiée, et une commande annulée ne peut pas être réactivée.

**Rembourser** une commande payée : depuis le Dashboard Stripe (*Paiements → la transaction → Rembourser*),
puis passez la commande en *Annulée* et remettez le stock à jour si les articles sont revenus.

### Factures

Créées automatiquement au paiement (numérotation continue `F2026-000123`). Lien PDF dans la fiche commande et dans
*Commandes & factures → Factures*. Le client les retrouve dans son espace et sur sa page de suivi.

---

## 4. Export comptable

*Commandes & factures → Commandes → bouton « Export comptable CSV par période »* (ou le compteur CA du tableau de bord).
Choisissez les dates (incluses) puis **Télécharger le CSV**. Le fichier s'ouvre directement dans Excel ou
LibreOffice et contient, pour chaque commande payée dans la période : date de paiement, n° de commande et de
facture, client, sous-total, remises club et promo, livraison, **HT, TVA, TTC**, référence de paiement Stripe.

---

## 5. Clubs et coachs

Les clients font leur demande depuis *Mon compte → Offre Club / Coach* (nom du club, SIRET, message) ;
vous recevez un e-mail.

*Clients & clubs → Clients*, filtre **statut club → En attente**. Vérifiez le SIRET (annuaire-entreprises.data.gouv.fr),
puis cochez le(s) client(s) et choisissez l'action **Valider le statut Club / Coach** ou **Refuser la demande**.
Le client est prévenu par e-mail ; une fois validé, la remise s'applique **automatiquement** dans son panier.

**Grille tarifaire** : *Clients & clubs → Grille tarifaire clubs*. Chaque palier = quantité minimale d'articles dans le
panier → pourcentage de remise (ex. 5 articles → −10 %). Le pourcentage est modifiable directement dans la liste.
La remise club s'applique avant le code promo.

---

## 6. Codes promo et livraison

*Panier & promotions → Codes promo → Ajouter* :
- **Code** (saisi en majuscules automatiquement), **type** pourcentage ou montant fixe en €, **valeur** ;
- **montant minimum** du panier, dates de validité, **nombre maximal d'utilisations** (vide = illimité) ;
- **actif** : décochez pour désactiver immédiatement.
Le compteur *utilisations* n'augmente qu'au paiement effectif.

*Paramètres boutique → Réglages de livraison* (une seule fiche) : nom du transporteur affiché, **forfait de livraison** et **seuil de
livraison offerte**. Le seuil s'apprécie après remises. Le changement est immédiat sur le site.

---

## 7. Référencement (SEO) des pages

- Produits, disciplines, types, guides : section **SEO** de chaque fiche.
- Pages fixes (accueil, boutique, guides…) : *Paramètres boutique → SEO des pages fixes* (chemin de la page, titre, description).

Bonnes pratiques : un titre unique par page avec le mot-clé principal (« Gants de boxe cuir 14 oz »), une
description qui donne envie de cliquer. Les données structurées (prix, stock, avis) sont générées automatiquement.

---

## 8. Questions fréquentes

**Un client n'a pas reçu son e-mail de confirmation.** Vérifiez l'adresse dans la commande et ses courriers
indésirables. Il peut retrouver sa commande sur *Suivi de commande* (n° + e-mail) et télécharger sa facture.

**Une commande est restée « En attente ».** Le client n'a pas finalisé le paiement : elle est annulée
automatiquement (au plus tard 48 h). Rien à faire, le stock n'a pas été touché.

**Un produit n'apparaît pas sur le site.** Vérifiez que le produit est *En ligne*, qu'il possède au moins une
déclinaison *active* (et, idéalement, une photo).

**Un client demande la suppression de ses données.** Il peut le faire lui-même dans *Mon compte → Mes données*.
Sinon, supprimez son compte dans *Clients & clubs → Clients* : ses commandes et factures restent conservées (obligation
légale). Voir `docs/RGPD.md`.
