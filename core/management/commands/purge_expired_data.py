"""Application des durées de conservation RGPD (à planifier chaque nuit, ex. cron).

    python manage.py purge_expired_data            # simulation : affiche ce qui serait supprimé
    python manage.py purge_expired_data --apply    # applique

Règles (cf. docs/RGPD.md et la politique de confidentialité) :
  - paniers non convertis : supprimés après 30 jours sans modification ;
  - commandes « en attente de paiement » : annulées après 48 h (paiement abandonné) ;
  - comptes clients inactifs depuis 3 ans (aucune connexion ni commande) : supprimés, avis anonymisés ;
  - événements Stripe techniques : supprimés après 90 jours.
Les commandes payées et les factures sont conservées 10 ans (obligation comptable) : jamais purgées ici.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from accounts.models import Customer
from cart.models import Cart
from catalog.models import Review
from orders.models import Order, StripeEvent


class Command(BaseCommand):
    help = "Purge les données dont la durée de conservation est dépassée."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Applique réellement les suppressions.")

    def handle(self, *args, apply=False, **options):
        now = timezone.now()
        carts = Cart.objects.filter(updated_at__lt=now - timedelta(days=30))
        pending = Order.objects.filter(status=Order.Status.PENDING, created_at__lt=now - timedelta(hours=48))
        events = StripeEvent.objects.filter(received_at__lt=now - timedelta(days=90))
        cutoff = now - timedelta(days=3 * 365)
        inactive = (
            Customer.objects.filter(is_staff=False, date_joined__lt=cutoff)
            .filter(Q(last_login__lt=cutoff) | Q(last_login__isnull=True))
            .annotate(last_order=Max("orders__created_at"))
            .filter(Q(last_order__lt=cutoff) | Q(last_order__isnull=True))
        )
        report = {
            "paniers > 30 j": carts.count(),
            "commandes en attente > 48 h": pending.count(),
            "comptes inactifs > 3 ans": inactive.count(),
            "événements Stripe > 90 j": events.count(),
        }
        for label, n in report.items():
            self.stdout.write(f"{label} : {n}")
        if not apply:
            self.stdout.write(self.style.WARNING("Simulation uniquement : relancez avec --apply pour appliquer."))
            return
        with transaction.atomic():
            carts.delete()
            pending.update(status=Order.Status.CANCELLED)
            events.delete()
            ids = list(inactive.values_list("pk", flat=True))
            Review.objects.filter(customer_id__in=ids).update(customer=None, author_name="Client anonyme")
            Order.objects.filter(customer_id__in=ids).update(customer=None)
            Customer.objects.filter(pk__in=ids).delete()
        self.stdout.write(self.style.SUCCESS("Purge appliquée."))
