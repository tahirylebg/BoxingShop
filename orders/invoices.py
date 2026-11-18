"""Génération des factures PDF avec WeasyPrint."""
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string

FONTS_DIR = Path(settings.BASE_DIR) / "assets" / "fonts"


class InvoiceUnavailable(Exception):
    pass


def vat_breakdown(order):
    rate = Decimal(settings.SHOP["vat_rate"])
    total_ht = (order.total / (1 + rate / 100)).quantize(Decimal("0.01"))
    return {"rate": rate, "total_ht": total_ht, "vat": order.total - total_ht}


def render_pdf(invoice):
    try:
        from weasyprint import HTML  # dépend de Pango (présent dans l'image Docker)
    except OSError as exc:  # bibliothèques système absentes (ex. Windows sans GTK)
        raise InvoiceUnavailable("WeasyPrint indisponible sur ce serveur.") from exc
    order = invoice.order
    html = render_to_string("orders/invoice_pdf.html", {
        "invoice": invoice, "order": order, "items": list(order.items.all()), "SHOP": settings.SHOP,
        "vat": vat_breakdown(order), "fonts_dir": FONTS_DIR.as_uri(),
    })
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()


def get_or_build_pdf(invoice):
    """Retourne les octets du PDF, générés une seule fois puis conservés (document comptable figé)."""
    if invoice.pdf:
        try:
            with invoice.pdf.open("rb") as fh:
                return fh.read()
        except FileNotFoundError:
            pass
    data = render_pdf(invoice)
    invoice.pdf.save(f"{invoice.number}.pdf", ContentFile(data), save=True)
    return data
