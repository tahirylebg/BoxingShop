"""Limitation de débit simple (fenêtre fixe) basée sur le cache Django."""
import functools
import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


def client_ip(request):
    # X-Real-IP n'est pris en compte que si l'appli est derrière un proxy de confiance (Nginx le positionne),
    # sinon il serait falsifiable par le client.
    if settings.RATELIMIT_TRUST_PROXY and request.META.get("HTTP_X_REAL_IP"):
        return request.META["HTTP_X_REAL_IP"]
    return request.META.get("REMOTE_ADDR", "")


def ratelimit(key, rate, methods=("POST",)):
    """Décorateur : `rate` = « 5/m », « 20/h ». Retourne HTTP 429 au-delà."""
    count, period = rate.split("/")
    limit = int(count)
    window = {"s": 1, "m": 60, "h": 3600, "d": 86400}[period]

    def decorator(view):
        @functools.wraps(view)
        def wrapped(request, *args, **kwargs):
            if settings.RATELIMIT_ENABLED and request.method in methods:
                bucket = int(time.time() // window)
                cache_key = f"rl:{key}:{client_ip(request)}:{bucket}"
                added = cache.add(cache_key, 1, window)
                hits = 1 if added else cache.incr(cache_key)
                if hits > limit:
                    response = HttpResponse(
                        "Trop de tentatives. Merci de patienter quelques minutes avant de réessayer.",
                        status=429, content_type="text/plain; charset=utf-8",
                    )
                    response["Retry-After"] = str(window)
                    return response
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
