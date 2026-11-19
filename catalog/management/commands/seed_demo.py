"""Initialise la base avec un jeu de démonstration réaliste.

    python manage.py seed_demo            # refuse si des produits existent déjà
    python manage.py seed_demo --reset    # supprime catalogue, commandes, paniers puis recrée tout

Les identifiants des comptes de démonstration sont lus dans l'environnement
(DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, DEMO_CUSTOMER_EMAIL, DEMO_CUSTOMER_PASSWORD) : aucun mot de passe
n'est écrit dans le code.
"""
import json
import os
import random
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import Address, ClubPriceTier, Customer
from cart.models import Cart, PromoCode
from catalog import demo_data as data
from catalog import demo_photos
from catalog.images import treat_photo
from core.models import HomeSettings, Photo
from catalog.demo_art import render
from catalog.models import (Category, Discipline, Product, ProductImage, Review, SizeChart, SizeChartRow,
                            Variant)
from content.models import Guide
from core.models import PageMeta, ShippingSettings
from orders.models import Invoice, Order, OrderItem, StripeEvent



# Photos de rayon : traitement Pillow commun, renditions WebP 400/800/1200, cadrage carré
CATEGORY_WIDTHS = (400, 800, 1200)
CATEGORY_PHOTOS = {"gants": "cat-gants", "protections": "cat-protections", "tenues": "cat-tenues",
                   "bandages-soins": "cat-bandages", "materiel-de-club": "cat-materiel"}
CATEGORY_FOCUS = {"cat-tenues": 0.82, "cat-protections": 0.3, "cat-materiel": 0.45}  # hauteur du centre d'intérêt


def square_crop(raw, focus_y=0.5):
    """Recadre en carré autour d'un centre d'intérêt vertical (0 = haut, 1 = bas)."""
    from io import BytesIO

    from PIL import Image

    with Image.open(BytesIO(raw)) as img:
        img = img.convert("RGB")
        side = min(img.size)
        left = (img.width - side) // 2
        top = int(max(0, min(img.height - side, focus_y * img.height - side / 2)))
        out = BytesIO()
        img.crop((left, top, left + side, top + side)).save(out, "JPEG", quality=92)
        return out.getvalue()

class Command(BaseCommand):
    help = "Crée ~30 produits de démonstration, 2 guides, 1 code promo, 1 admin et 1 client de test."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Supprime les données existantes avant.")

    def handle(self, *args, reset=False, **options):
        creds = {k: os.environ.get(k) for k in (
            "DEMO_ADMIN_EMAIL", "DEMO_ADMIN_PASSWORD", "DEMO_CUSTOMER_EMAIL", "DEMO_CUSTOMER_PASSWORD")}
        missing = [k for k, v in creds.items() if not v]
        if missing:
            raise CommandError(f"Variables d'environnement manquantes : {', '.join(missing)} (voir .env.example).")
        if Product.objects.exists() and not reset:
            raise CommandError("Des produits existent déjà. Relancez avec --reset pour tout recréer.")

        with transaction.atomic():
            if reset:
                self._reset()
            self.rng = random.Random(42)
            self._settings()
            self.photos = self._photo_library()
            self._home()
            self._category_photos()
            disciplines = self._disciplines()
            categories = self._categories()
            charts = self._size_charts(categories)
            products = self._products(disciplines, categories, charts)
            self._guides(products, categories)
            self._reviews(products)
            self._age_catalog()
            admin, client = self._accounts(creds)
            self._orders(client, products)

        low = Variant.objects.low_stock().count()
        self.stdout.write(self.style.SUCCESS(
            f"OK : {len(products)} produits, {Variant.objects.count()} SKU ({low} sous le seuil), "
            f"{Guide.objects.count()} guides, code promo RING10, comptes {admin.email} / {client.email}."
        ))

    # ------------------------------------------------------------------------------------------
    def _reset(self):
        for model in (StripeEvent, Invoice, OrderItem, Order, Cart, Review, Guide, ProductImage, Variant, Product,
                      SizeChartRow, SizeChart, PromoCode, ClubPriceTier, PageMeta):
            model.objects.all().delete()
        HomeSettings.objects.update(hero_photo=None, campaign_photo=None, guides_photo=None)
        Photo.objects.all().delete()
        Category.objects.filter(parent__isnull=False).delete()
        Category.objects.all().delete()
        Discipline.objects.all().delete()

    def _settings(self):
        s = ShippingSettings.load()
        s.flat_rate, s.free_shipping_threshold = Decimal("6.90"), Decimal("90.00")
        s.save()
        PromoCode.objects.create(
            code="RING10", description="Bienvenue : -10 % dès 50 €", discount_type="percent", value=Decimal("10"),
            min_subtotal=Decimal("50"), valid_from=timezone.now() - timedelta(days=1),
            valid_until=timezone.now() + timedelta(days=365),
        )
        for qty, pct in ((5, "10"), (10, "15"), (20, "20")):
            ClubPriceTier.objects.create(min_quantity=qty, discount_percent=Decimal(pct))
        for path, label, title, desc in data.PAGE_META:
            PageMeta.objects.create(path=path, label=label, meta_title=title, meta_description=desc)

    # --- Photos ---------------------------------------------------------------------------------
    def _photo_library(self):
        """Crée la photothèque à partir de media/demo (scripts/fetch_photos.py), traitement éditorial appliqué."""
        demo = settings.MEDIA_ROOT / "demo"
        credits_file = demo / "credits.json"
        self.photo_meta = {}
        if not credits_file.exists():
            self.stdout.write(self.style.WARNING(
                "Aucune photo : lancez `python scripts/fetch_photos.py` (visuels de secours utilisés)."))
            return {}
        library = {}
        for i, c in enumerate(json.loads(credits_file.read_text("utf-8"))):
            src = demo / ("categories" if c["key"].startswith("cat-") else "originals") / f"{c['key']}.jpg"
            if not src.exists():
                continue
            raw = src.read_bytes()
            self.photo_meta[c["key"]] = (c, raw)
            photo = Photo(title=c["alt"][:120], alt=c["alt"], credit=c["author"], credit_source=c["source"],
                          credit_url=c["page"])
            if c["key"].startswith("cat-"):
                photo.RENDITION_WIDTHS = CATEGORY_WIDTHS
                raw = square_crop(raw, CATEGORY_FOCUS.get(c["key"], 0.5))
            photo.image.save(f"{c['key']}.jpg", ContentFile(treat_photo(raw, mode="editorial", seed=i)), save=False)
            photo.save()
            library[c["key"]] = photo
        self.stdout.write(f"Photothèque : {len(library)} photos.")
        return library

    def _category_photos(self):
        """Une photo d'objet par rayon racine (tuiles « Rayon par rayon »)."""
        for slug, key in CATEGORY_PHOTOS.items():
            if key in self.photos:
                Category.objects.filter(slug=slug, parent__isnull=True).update(photo=self.photos[key])

    def _first_photo(self, keys):
        found = demo_photos.pick(keys, self.photos)
        return self.photos[found[0]] if found else None

    def _home(self):
        home = HomeSettings.load()
        used = set()
        for field, prefs, label, seed in (("hero_photo", demo_photos.HERO, "Hero", 7),
                                          ("campaign_photo", demo_photos.CAMPAIGN, "Campagne", 11),
                                          ("guides_photo", demo_photos.GUIDES_HERO, "Guides", 13)):
            key = next((k for k in demo_photos.pick(prefs, self.photos, count=len(prefs)) if k not in used), None)
            if not key:
                continue
            used.add(key)
            c, raw = self.photo_meta[key]
            photo = Photo(title=f"{label} — {c['alt']}"[:120], alt="", credit=c["author"],
                          credit_source=c["source"], credit_url=c["page"])
            photo.image.save(f"{label.lower()}-{key}.jpg",
                             ContentFile(treat_photo(raw, mode="bw", max_width=2400, seed=seed)), save=False)
            photo.save()
            setattr(home, field, photo)
        home.save()

    def _disciplines(self):
        out = {}
        for i, (slug, name, short, tagline, desc) in enumerate(data.DISCIPLINES):
            out[slug] = Discipline.objects.create(slug=slug, name=name, short_name=short, tagline=tagline,
                                                  description=desc, position=i,
                                                  photo=self._first_photo(demo_photos.DISCIPLINES.get(slug, [])))
        return out

    def _categories(self):
        out = {}
        for i, (slug, name, parent) in enumerate(data.CATEGORIES):
            out[slug] = Category.objects.create(slug=slug, name=name, parent=out.get(parent), position=i)
        return out

    def _size_charts(self, categories):
        out = {}
        for c in data.SIZE_CHARTS:
            chart = SizeChart.objects.create(name=c["name"], category=categories.get(c["category"]),
                                             measure_label=c["measure"], intro=c["intro"])
            for i, (wmin, wmax, hmin, hmax, rec, note) in enumerate(c["rows"]):
                SizeChartRow.objects.create(chart=chart, body_weight_min=wmin, body_weight_max=wmax, height_min=hmin,
                                            height_max=hmax, recommended=rec, note=note, position=i)
            out[c["key"]] = chart
        return out

    def _products(self, disciplines, categories, charts):
        products = {}
        for spec in data.PRODUCTS:
            product = Product.objects.create(
                name=spec["name"], slug=spec["slug"], discipline=disciplines[spec["disc"]],
                category=categories[spec["cat"]], short_description=spec["short"], description=spec["desc"],
                material=spec["material"], level=spec["level"], range_tier=spec.get("range", "standard"),
                padding=spec.get("padding", ""), closure=spec.get("closure", ""), origin=spec.get("origin", ""),
                extra_specs=spec.get("extra", {}), is_featured=spec.get("featured", False),
                size_chart=charts.get(spec.get("chart")),
                meta_description=spec["short"][:160],
            )
            Product.objects.filter(pk=product.pk).update(sales_count=spec.get("sales", 0))
            product.disciplines.add(product.discipline, *[disciplines[d] for d in spec.get("also", [])])
            self._variants(product, spec)
            self._images(product, spec)
            products[spec["slug"]] = product
        return products

    def _variants(self, product, spec):
        axis = spec.get("weights") or spec.get("sizes") or [None]
        base = Decimal(str(spec["price"]))
        low_budget = 2 if spec.get("low") else 0
        for color, hex_ in spec["colors"]:
            for i, opt in enumerate(axis):
                is_weight = "weights" in spec
                price = base + Decimal(spec.get("step", 0)) * i
                stock = self.rng.choice([6, 9, 12, 15, 20, 25, 30]) if self.rng.random() > 0.04 else 0
                if low_budget and stock:
                    stock, low_budget = self.rng.choice([1, 2, 3]), low_budget - 1
                suffix = f"{opt:02d}" if is_weight else (opt or "U")
                Variant.objects.create(
                    product=product, sku=f"BS-{spec['code']}-{color[:3].upper()}-{suffix}", color=color,
                    color_hex=hex_, weight_oz=opt if is_weight else None, size="" if is_weight else (opt or ""),
                    price=price, compare_at_price=(price * Decimal("1.2")).quantize(Decimal("1")) - Decimal("0.10")
                    if spec["slug"] in {"gant-sparring-microfibre", "short-gala-satin"} else None,
                    stock=stock, low_stock_threshold=3,
                )

    def _images(self, product, spec):
        cat_label = product.category.name
        index = list(data.PRODUCTS).index(spec)
        keys = demo_photos.pick(demo_photos.SHAPES.get(spec["shape"], []), self.photos, offset=index, count=2)
        for pos, key in enumerate(keys):
            c, raw = self.photo_meta[key]
            img = ProductImage(product=product, alt=c["alt"], position=pos,
                               credit=f"{c['author']} · {c['source']}")
            img.image.save(f"{spec['slug']}-photo-{pos + 1}.jpg",
                           ContentFile(treat_photo(raw, mode="editorial", max_width=1400, crop=0.8, seed=index)),
                           save=False)
            img.save()
        offset = len(keys)
        for pos, (color, hex_) in enumerate(spec["colors"], start=offset):
            caption = f"{spec['code']} · {color} · {cat_label}"
            png = render(spec["shape"], hex_, caption)
            img = ProductImage(product=product, alt=f"{product.name}, coloris {color.lower()}", color=color,
                               position=pos, credit="Visuel Boxing Shop")
            img.image.save(f"{spec['slug']}-{color.lower()}.png", ContentFile(png), save=False)
            img.save()

    def _guides(self, products, categories):
        for i, g in enumerate(data.GUIDES):
            guide = Guide.objects.create(
                slug=g["slug"], title=g["title"], kicker=g["kicker"], excerpt=g["excerpt"], body=g["body"],
                reading_minutes=g["minutes"], topic=g.get("topic", "gants"), published_at=date.today() - timedelta(days=20 * (i + 1)),
                meta_description=g["excerpt"][:160],
            )
            guide.photo = self._first_photo(demo_photos.GUIDES.get(g["slug"], []))
            guide.save(update_fields=["photo"])
            guide.products.set([products[s] for s in g["products"]])
            guide.categories.set([categories[s] for s in g["categories"]])

    def _age_catalog(self):
        """Le catalogue de démo n'est pas « tout neuf » : seuls 5 produits gardent le badge Nouveau."""
        from datetime import timedelta

        from django.utils import timezone

        fresh = list(Product.objects.order_by("-id")
                     .values_list("pk", flat=True)[:5])
        Product.objects.exclude(pk__in=fresh).update(created_at=timezone.now() - timedelta(days=120))

    def _reviews(self, products):
        for slug, author, rating, title, body in data.REVIEWS:
            Review.objects.create(product=products[slug], author_name=author, rating=rating, title=title, body=body,
                                  is_published=True)

    def _accounts(self, creds):
        Customer.objects.filter(email__in=[creds["DEMO_ADMIN_EMAIL"], creds["DEMO_CUSTOMER_EMAIL"]]).delete()
        admin = Customer.objects.create_superuser(creds["DEMO_ADMIN_EMAIL"], creds["DEMO_ADMIN_PASSWORD"],
                                                  first_name="Admin", last_name="Boxing Shop")
        client = Customer.objects.create_user(creds["DEMO_CUSTOMER_EMAIL"], creds["DEMO_CUSTOMER_PASSWORD"],
                                              first_name="Sam", last_name="Durand", phone="06 12 34 56 78")
        Address.objects.create(customer=client, label="Domicile", first_name="Sam", last_name="Durand",
                               line1="8 boulevard de Belleville", postal_code="75011", city="Paris", is_default=True)
        return admin, client

    def _orders(self, client, products):
        address = client.addresses.first()
        history = [
            (Order.Status.DELIVERED, 40, [("gant-cuir-heritage-pro", 0, 1), ("bandes-de-boxe-450", 0, 2)]),
            (Order.Status.SHIPPED, 3, [("protege-tibias-cuir-pro", 1, 1), ("short-muay-thai-traditionnel", 2, 1)]),
        ]
        for status, days_ago, lines in history:
            when = timezone.now() - timedelta(days=days_ago)
            items = []
            for slug, idx, qty in lines:
                variant = list(products[slug].variants.all())[idx]
                items.append((variant, qty))
            subtotal = sum(v.price * q for v, q in items)
            shipping = Decimal("0") if subtotal >= 90 else Decimal("6.90")
            order = Order.objects.create(
                customer=client, email=client.email, status=status, first_name=address.first_name,
                last_name=address.last_name, line1=address.line1, postal_code=address.postal_code, city=address.city,
                subtotal=subtotal, shipping_cost=shipping, total=subtotal + shipping, paid_at=when,
                carrier="Colissimo", tracking_number=f"6A{self.rng.randint(10**10, 10**11 - 1)}",
                shipped_at=when + timedelta(days=1),
                delivered_at=when + timedelta(days=3) if status == Order.Status.DELIVERED else None,
            )
            Order.objects.filter(pk=order.pk).update(created_at=when)
            for v, q in items:
                OrderItem.objects.create(order=order, variant=v, product_name=v.product.name, variant_label=v.label,
                                         sku=v.sku, unit_price=v.price, quantity=q, line_total=v.price * q)
            Invoice.objects.create(order=order, issued_at=when)
