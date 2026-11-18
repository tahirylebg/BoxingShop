# Registre RGPD — Boxing Shop

Document interne (article 30 du RGPD). À tenir à jour à chaque nouveau traitement ou prestataire.
La version publique figure sur la page `/informations/confidentialite/`.

## Traitements et durées de conservation

| Données | Finalité | Base légale | Durée | Mise en œuvre |
|---|---|---|---|---|
| Identité, e-mail, téléphone, adresses | Compte client | Contrat | Jusqu'à suppression, ou **3 ans** sans connexion ni commande | Suppression en libre-service ; purge automatique `purge_expired_data` |
| Commandes, factures, adresse de livraison | Exécution, comptabilité | Obligation légale | **10 ans** (art. L123-22 C. com.) | Jamais purgées ; détachées du compte s'il est supprimé ; non supprimables dans l'admin |
| Commandes non payées | Paiement abandonné | Intérêt légitime | **48 h** puis annulation | `purge_expired_data` (+ webhook `checkout.session.expired`) |
| Paniers non commandés | Conservation du panier | Intérêt légitime | **30 jours** sans modification | `purge_expired_data` |
| Avis produits | Publication | Consentement | Durée du compte, puis **anonymisés** | Suppression du compte / purge |
| Statut Club/Coach (club, SIRET, message) | Tarifs clubs | Contrat | Durée du compte | Supprimés avec le compte |
| Événements Stripe (identifiant, type) | Idempotence des paiements | Intérêt légitime | **90 jours** | `purge_expired_data` |
| Session, jeton CSRF, choix cookies | Fonctionnement, sécurité | Strictement nécessaire | Session 14 j · choix cookies **6 mois** | Expiration des cookies |
| Journaux serveur (IP) | Sécurité | Intérêt légitime | **12 mois** max. | Rotation logrotate / hébergeur |

Planification de la purge (chaque nuit) :

```bash
python manage.py purge_expired_data          # simulation : affiche les volumes concernés
python manage.py purge_expired_data --apply  # exécution
```

## Cookies

Seuls des cookies **strictement nécessaires** sont déposés (session, CSRF, mémorisation du choix). Aucun outil
de mesure d'audience ni traceur publicitaire n'est installé. La bannière propose « Refuser » et « Accepter » au
même niveau ; le choix est mémorisé 6 mois et modifiable sur `/cookies/`. Si un outil de mesure est ajouté,
il ne doit être chargé que lorsque `cookie_consent == "accepted"` (variable disponible dans tous les templates).

## Droits des personnes

| Droit | Comment |
|---|---|
| Accès / portabilité | *Mon compte → Mes données → Télécharger (JSON)* : profil, adresses, commandes, avis |
| Rectification | *Mon compte → Profil* et *Carnet d'adresses* |
| Effacement | *Mon compte → Mes données → Supprimer mon compte* (mot de passe demandé). Compte, adresses, paniers supprimés ; avis anonymisés ; commandes conservées sans lien avec le compte |
| Demandes par e-mail | Traiter sous 1 mois. Clients invités : retrouver les commandes par e-mail dans l'admin (*Commandes & factures → Commandes*, recherche) |

## Sous-traitants

| Prestataire | Données | Localisation / garanties |
|---|---|---|
| Stripe | E-mail, montant, moyen de paiement (saisi chez Stripe) | UE/US — clauses contractuelles types, DPA Stripe |
| Hébergeur | Ensemble de la base | À renseigner (privilégier l'UE) |
| Prestataire e-mail (SMTP) | E-mail, contenu des messages transactionnels | À renseigner |
| Transporteur | Nom, adresse, téléphone | Transmis lors de l'expédition |
| API Adresse (IGN) | Texte saisi dans le champ adresse uniquement | Service public français, sans cookie |

## Sécurité

Mots de passe hachés (PBKDF2), HTTPS forcé avec HSTS, cookies `Secure`/`HttpOnly`/`SameSite`, CSP stricte,
limitation des tentatives de connexion, factures accessibles uniquement au client (jeton) ou au staff,
aucune donnée de carte bancaire stockée (paiement sur l'infrastructure Stripe, PCI-DSS).
