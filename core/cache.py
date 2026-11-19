"""Cache des données de navigation et du catalogue, invalidé par signaux à chaque modification."""
from django.conf import settings
from django.core.cache import cache

VERSION_KEY = "catalog:version"
# À incrémenter quand la forme des données mises en cache change (déploiement de code).
SCHEMA = 3


def catalog_version():
    version = cache.get(VERSION_KEY)
    if version is None:
        version = 1
        cache.set(VERSION_KEY, version, None)
    return version


def bump_catalog_version(*args, **kwargs):
    try:
        cache.incr(VERSION_KEY)
    except ValueError:
        cache.set(VERSION_KEY, 2, None)


def cached(key, builder, timeout=None):
    """Mémorise builder() sous une clé versionnée (toute modification du catalogue l'invalide)."""
    full_key = f"{key}:s{SCHEMA}:v{catalog_version()}"
    value = cache.get(full_key)
    if value is None:
        value = builder()
        cache.set(full_key, value, timeout or settings.CATALOG_CACHE_TIMEOUT)
    return value
