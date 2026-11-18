from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import Cart
from .services import SESSION_KEY, merge_carts


@receiver(user_logged_in)
def merge_guest_cart(sender, request, user, **kwargs):
    cart_id = request.session.pop(SESSION_KEY, None)
    if not cart_id:
        return
    guest = Cart.objects.filter(pk=cart_id, customer__isnull=True).first()
    if guest is None:
        return
    target = Cart.objects.filter(customer=user).order_by("-updated_at").first()
    if target is None:
        guest.customer = user
        guest.save(update_fields=["customer"])
    else:
        merge_carts(guest, target)
    request.session["cart_count"] = sum(i.quantity for i in (target or guest).items.all())
