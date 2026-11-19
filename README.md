# Boxing Shop

E-commerce d'équipement de boxe et d'arts martiaux — Django 5.2 LTS, PostgreSQL, Stripe Checkout,
rendu serveur en HTML5/CSS3 pur (aucun framework CSS ni JS), direction artistique « Brutalist Gym & Heritage ».

| | |
|---|---|
| **Stack** | Python 3.12 · Django 5.2 · PostgreSQL 16 · Stripe Checkout · WeasyPrint · Pillow (WebP) · django-environ |
| **Front** | Templates Django, CSS3 maison (`static/css/main.css`), 4 modules JS vanilla optionnels |
| **Qualité** | 76 tests pytest-django · Lighthouse 97–100 / 100 / 100 / 100 (mobile & desktop) |

---

## Sommaire
1. [Installation rapide (Docker)](#1-installation-rapide-docker)
2. [Installation locale (sans Docker pour Django)](#2-installation-locale)
3. [Variables d'environnement](#3-variables-denvironnement)
4. [Données de démonstration et identifiants](#4-données-de-démonstration)
5. [Paiement Stripe en mode test](#5-paiement-stripe-en-mode-test)
6. [Tests](#6-tests)
7. [Déploiement en production](#7-déploiement-en-production)
8. [Architecture](#8-architecture)
9. [Sécurité, RGPD, performance](#9-sécurité-rgpd-performance)

Documentation complémentaire : [`docs/GUIDE_BACKOFFICE.md`](docs/GUIDE_BACKOFFICE.md) (équipe boutique, non-développeurs)
et [`docs/RGPD.md`](docs/RGPD.md) (registre des traitements, durées de conservation).

---

## 1. Installation rapide (Docker)

Prérequis : Docker Desktop.

```bash
cp .env.example .env                      # puis renseigner SECRET_KEY (voir commentaire dans le fichier)
docker compose up -d --build              # PostgreSQL (port hôte 5433) + Django sur http://localhost:8000
docker compose exec web python manage.py seed_demo
```

Le conteneur `web` applique les migrations et crée la table de cache au démarrage.
L'image contient les bibliothèques Pango nécessaires à WeasyPrint : les factures PDF fonctionnent directement.

## 2. Installation locale

Prérequis : Python 3.12, Docker (pour PostgreSQL uniquement) ou un PostgreSQL ≥ 14.

```bash
python -m venv .venv
source .venv/bin/activate                 # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                      # DATABASE_URL pointe déjà sur localhost:5433
docker compose up -d db
python manage.py migrate
python manage.py createcachetable
python manage.py seed_demo
python manage.py runserver
```

**Factures PDF hors Docker** : WeasyPrint nécessite Pango.
macOS `brew install pango` · Debian/Ubuntu `apt install libpango-1.0-0 libpangoft2-1.0-0` ·
Windows : installer [MSYS2](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows) ou utiliser Docker.
Sans Pango, le site fonctionne et le lien de facture renvoie une page « momentanément indisponible » (HTTP 503).

## 3. Variables d'environnement

Toutes sont lues par `django-environ` depuis `.env` (voir `.env.example`, commenté).

| Variable | Rôle | Défaut |
|---|---|---|
| `SECRET_KEY` | Clé Django — **obligatoire**, unique par environnement | — |
| `DEBUG` | Mode debug (jamais en production) | `False` |
| `DJANGO_SETTINGS_MODULE` | `boxingshop.settings.dev` / `.prod` / `.test` | `dev` (manage.py), `prod` (wsgi) |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Domaines autorisés (séparés par des virgules) | `localhost` |
| `SITE_URL` | URL publique (retours Stripe, e-mails, canonical) | `http://localhost:8000` |
| `DATABASE_URL` | Connexion PostgreSQL | — |
| `CACHE_URL` | Cache partagé : `dbcache://boxingshop_cache` ou `redis://…` | dbcache |
| `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` | Clés API Stripe | — |
| `STRIPE_WEBHOOK_SECRET` | Secret de signature du webhook (`whsec_…`) | — |
| `EMAIL_*`, `DEFAULT_FROM_EMAIL` | SMTP d'envoi | console |
| `SHOP_ADMIN_EMAIL` | Destinataire des alertes (stock bas, demandes club, anomalies paiement) | — |
| `SHOP_LEGAL_NAME`, `SHOP_ADDRESS`, `SHOP_SIRET`, `SHOP_VAT`, `SHOP_CONTACT_EMAIL` | Mentions légales et factures | valeurs fictives |
| `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` | HTTPS forcé (prod) | `True`, 1 an |
| `RATELIMIT_TRUST_PROXY` | Lire l'IP client dans `X-Real-IP` (derrière Nginx) | `True` en prod |
| `MEDIA_ROOT` | Dossier des images téléversées | `./media` |
| `SERVE_MEDIA` | Django sert `/media/` (audit local en mode prod uniquement) | `False` |
| `DEMO_*` | Comptes créés par `seed_demo` — **jamais lus par le code applicatif** | — |
| `PEXELS_API_KEY`, `UNSPLASH_ACCESS_KEY` | Facultatives : crédits Pexels, photos Unsplash (`fetch_photos.py`) | — |

## 4. Données de démonstration

```bash
python scripts/fetch_photos.py        # 1. photos libres de droits → media/demo/ (+ CREDITS.md)
python manage.py seed_demo            # 2. catalogue, photothèque, comptes
python manage.py seed_demo --reset    #    repart d'un catalogue vierge
```

**Photos** : `scripts/fetch_photos.py` télécharge des photos Pexels (sans clé) et, si `UNSPLASH_ACCESS_KEY` est
défini, des photos Unsplash via l'API officielle. Chaque fichier est vérifié (HTTP, type, Pillow, largeur) ; les
auteurs sont listés dans [`CREDITS.md`](CREDITS.md) et en légende discrète sur le site. Au seed, un traitement
Pillow unifie l'ambiance (légère désaturation + contraste ; hero en noir et blanc granuleux) puis le site génère
les déclinaisons WebP (`srcset`). Sans photo disponible, un visuel illustré de secours est utilisé : aucune
image cassée. Les photos illustrent l'univers et ne représentent pas forcément le produit exact ; chaque fiche
contient aussi des visuels par coloris.

Crée 5 disciplines, 5 types, **34 produits / 227 SKU** (dont 20 sous le seuil d'alerte) avec visuels générés,
tableaux de tailles, 2 guides techniques liés aux produits, avis, paliers club (5/10/20 articles → −10/−15/−20 %),
le code promo **`RING10`** (−10 % dès 50 €) et deux commandes payées avec facture pour le client.

| Rôle | E-mail | Mot de passe | Accès |
|---|---|---|---|
| Administrateur | `admin@boxingshop.local` | `Ring-Admin-2026!` | http://localhost:8000/admin/ |
| Client | `client@boxingshop.local` | `Ring-Client-2026!` | http://localhost:8000/compte/ |

Ces identifiants proviennent des variables `DEMO_*` du `.env` : modifiez-les à volonté ; la commande refuse
de s'exécuter si elles sont absentes. **Ne lancez jamais `seed_demo` en production.**

## 5. Paiement Stripe en mode test

1. Créez un compte Stripe et copiez les clés **de test** dans `.env` (`sk_test_…`, `pk_test_…`).
2. Installez la [Stripe CLI](https://docs.stripe.com/stripe-cli) puis relayez les webhooks vers le poste local :
   ```bash
   stripe login
   stripe listen --forward-to localhost:8000/commande/webhook/stripe/ \
     --events checkout.session.completed,checkout.session.async_payment_succeeded,checkout.session.async_payment_failed,checkout.session.expired
   ```
   Copiez le `whsec_…` affiché dans `STRIPE_WEBHOOK_SECRET` et redémarrez le serveur.
3. Passez commande avec la carte `4242 4242 4242 4242`, date future, CVC quelconque.
   Cartes utiles : `4000 0000 0000 9995` (refus fonds insuffisants), `4000 0025 0000 3155` (3-D Secure).

**Cycle d'une commande** : le tunnel crée une commande « en attente » et une session Stripe Checkout (remises
transmises sous forme de coupon à usage unique). **Le stock n'est décrémenté qu'à la réception du webhook
signé** `checkout.session.completed`, dans une transaction qui verrouille la commande puis les SKU
(`select_for_update`, ordre de clé stable). Si un article est épuisé entre-temps, la commande est annulée et
remboursée automatiquement. Chaque événement Stripe est enregistré (`StripeEvent`) : un rejeu est ignoré.
Un montant payé différent du total de la commande bloque la validation et alerte l'administrateur.

**Apple Pay / Google Pay** : aucun code supplémentaire. Activez-les dans *Dashboard Stripe → Paramètres →
Moyens de paiement* ; ils apparaissent automatiquement sur la page Checkout (Apple Pay : sur Safari avec une
carte enregistrée ; en production le domaine est géré par Stripe puisque le paiement a lieu sur `checkout.stripe.com`).

**Production** : créez un endpoint webhook dans *Dashboard → Développeurs → Webhooks* vers
`https://votre-domaine/commande/webhook/stripe/` avec les 4 événements ci-dessus, et utilisez son secret.

## 6. Tests

```bash
docker compose up -d db
pytest                         # 76 tests, ~20 s
pytest tests/test_checkout_webhook.py -v
```

Les tests utilisent PostgreSQL (verrous `select_for_update` réels) et `boxingshop.settings.test`
(e-mails en mémoire, Stripe simulé, cache local). Couverture fonctionnelle :

| Fichier | Contenu |
|---|---|
| `test_pricing.py` | livraison (forfait, seuil exact, seuil après remises), codes promo (%, montant, minimum, dates, quota), paliers club |
| `test_cart.py` | ajout, limites de stock, code promo via les vues, remise club, fusion du panier invité à la connexion |
| `test_checkout_webhook.py` | tunnel → session Stripe (mock), webhook signé : paiement, **décrément du stock**, idempotence, signature invalide, montant incohérent, expiration, rupture → annulation + remboursement, usage du code promo |
| `test_permissions.py` | pages compte, commandes et factures d'autrui, carnet d'adresses, admin réservé au staff, suppression de commandes interdite, auto-attribution du statut club, CSRF, rate-limit login/checkout, open-redirect, suppression de compte, en-têtes de sécurité, échappement XSS |
| `test_pages.py` | pages publiques, filtres sans JS, fragment AJAX, JSON-LD, URL canoniques, cookies, sitemap/robots |

## 7. Déploiement en production

Réglages : `DJANGO_SETTINGS_MODULE=boxingshop.settings.prod` (HTTPS forcé, HSTS 1 an, cookies
`__Secure-` Secure/HttpOnly/SameSite, templates en cache). Vérifiez avec `python manage.py check --deploy`.

### Option A — VPS : Gunicorn + Nginx

```bash
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=boxingshop.settings.prod
python manage.py migrate && python manage.py createcachetable && python manage.py collectstatic --noinput
gunicorn boxingshop.wsgi:application --bind 127.0.0.1:8000 --workers 3 --access-logfile -
```

Exemple de configuration Nginx : [`deploy/nginx.conf`](deploy/nginx.conf) (TLS, compression, `/media/` servi
directement avec cache immuable — les rendus WebP portent une empreinte de contenu —, en-tête `X-Real-IP`).
Gunicorn se lance idéalement via systemd (`Restart=always`).

Tâche planifiée quotidienne (cron) pour les durées de conservation RGPD :
```cron
30 3 * * * cd /srv/boxingshop && .venv/bin/python manage.py purge_expired_data --apply
```

### Option B — PaaS (Render, Railway, Scalingo, Fly.io…)

Utilisez le `Dockerfile` fourni (Gunicorn, utilisateur non-root, Pango inclus), une base PostgreSQL managée
et un **stockage persistant pour `/app/media`** (volume ou S3 via `django-storages`). Commande de release :
`python manage.py migrate && python manage.py createcachetable && python manage.py collectstatic --noinput`.
Les fichiers statiques sont servis compressés et versionnés par WhiteNoise.

## 8. Architecture

```
boxingshop/   settings (base, dev, prod, test), urls, wsgi
core/         accueil, pages légales, cookies, sitemap/robots, CSP & en-têtes, rate-limit, cache, admin du site,
              réglages livraison, SEO des pages, commande purge_expired_data
accounts/     client (connexion par e-mail), adresses, statut Club/Coach, paliers tarifaires, RGPD
catalog/      disciplines, types, produits, SKU, images WebP, tableaux de tailles, avis, filtres, seed_demo
content/      guides techniques (liés aux produits dans les deux sens)
cart/         panier, codes promo, calcul (pricing.py, fonction pure), tiroir
orders/       commandes, Stripe (services.py, webhook), e-mails, factures PDF, admin avancé
templates/    HTML5 sémantique · static/css/main.css · static/js/*.js (modules ES)
tests/        pytest-django
```

**URLs sémantiques** : `/boxe-anglaise/gants/gant-cuir-heritage-pro/` (produit), `/boxe-anglaise/`,
`/equipement/gants/`, `/boxe-anglaise/gants/`, `/boutique/?poids=14&matiere=cuir`, `/guides/<slug>/`.

**JavaScript (optionnel, amélioration progressive)** — 4 modules, conformément au cahier des charges :
`variant-picker.js` (prix, stock, SKU), `filters.js` (fetch + `pushState`), `cart-drawer.js` (tiroir `<dialog>`),
`address-autocomplete.js` (API Adresse de l'IGN). Sans JS : formulaires GET/POST classiques, le site reste complet.

## 9. Sécurité, RGPD, performance

- **OWASP** : CSRF partout (seul le webhook en est exempté, authentifié par signature HMAC Stripe), échappement
  automatique sans `|safe` sur des données utilisateur, ORM exclusivement, CSP stricte (`script-src 'self'`,
  `style-src 'self'`, sans `unsafe-inline` côté boutique), `X-Frame-Options`, `nosniff`, `Referrer-Policy`,
  `Permissions-Policy`, COOP/CORP ; rate-limit sur connexion (5/min), inscription, mot de passe oublié,
  checkout (10/min), suivi de commande et avis ; redirections `next` validées.
- **Contrôle d'accès** : commandes consultables par leur propriétaire ou via un jeton UUID secret (invités) ;
  commandes et factures non supprimables depuis l'admin (pièces comptables).
- **RGPD** : bannière cookies (refuser aussi simple qu'accepter ; seuls des cookies techniques sont déposés),
  export JSON et suppression du compte en libre-service, purge automatique, registre dans [`docs/RGPD.md`](docs/RGPD.md).
- **Performance** : images WebP 360→1400 px en `srcset`, lazy-loading hors première rangée, polices auto-hébergées
  préchargées, CSS unique, cache du catalogue invalidé par signaux, statiques compressés et versionnés.
- **Accessibilité** : WCAG 2.2 AA — contrastes vérifiés, focus visible, cibles ≥ 44 px, liens d'évitement,
  combobox ARIA, `<dialog>` natif, tableaux légendés.
