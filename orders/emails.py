"""E-mails transactionnels (texte + HTML)."""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, mail_admins
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _send(to, subject, template, context):
    context = {**context, "SHOP": settings.SHOP, "SITE_URL": settings.SITE_URL}
    text = render_to_string(f"emails/{template}.txt", context)
    html = render_to_string(f"emails/{template}.html", context)
    message = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [to])
    message.attach_alternative(html, "text/html")
    try:
        message.send()
    except Exception:  # un e-mail en échec ne doit jamais annuler une commande payée
        logger.exception("Échec d'envoi de l'e-mail « %s » à %s", subject, to)


def send_order_confirmation(order):
    _send(order.email, f"Commande {order.number} confirmée", "order_confirmation",
          {"order": order, "items": list(order.items.all())})


def send_order_shipped(order):
    _send(order.email, f"Commande {order.number} expédiée", "order_shipped", {"order": order})


def send_order_cancelled_stock(order):
    _send(order.email, f"Commande {order.number} annulée et remboursée", "order_cancelled", {"order": order})


def send_club_status(customer):
    _send(customer.email, "Votre statut Club / Coach", "club_status", {"customer": customer})


def notify_admin_low_stock(variant_ids):
    from catalog.models import Variant

    low = list(Variant.objects.low_stock().filter(pk__in=variant_ids).select_related("product"))
    if not low:
        return
    body = "\n".join(f"- {v.sku} {v.product.name} ({v.label}) : {v.stock} en stock (seuil {v.low_stock_threshold})"
                     for v in low)
    _send_admin("Alerte stock bas", f"Déclinaisons passées sous le seuil critique :\n\n{body}")


def notify_admin_payment_mismatch(order, amount_total):
    _send_admin(f"Montant de paiement incohérent — {order.number}",
                f"Stripe a encaissé {amount_total / 100:.2f} € pour une commande de {order.total} €. "
                "La commande reste en attente : vérification manuelle requise.")


def _send_admin(subject, body):
    try:
        if settings.ADMINS:
            mail_admins(subject, body)
        else:
            EmailMultiAlternatives(f"[Boxing Shop] {subject}", body, settings.DEFAULT_FROM_EMAIL,
                                   [settings.SHOP_ADMIN_EMAIL]).send()
    except Exception:
        logger.exception("Échec d'envoi de la notification admin « %s »", subject)
