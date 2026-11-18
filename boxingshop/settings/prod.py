from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# HTTPS forcé (derrière Nginx / un PaaS qui termine TLS)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__Secure-sessionid"
CSRF_COOKIE_NAME = "__Secure-csrftoken"

TEMPLATES[0]["APP_DIRS"] = False  # noqa: F405 — requis pour définir les loaders
TEMPLATES[0]["OPTIONS"]["loaders"] = [  # noqa: F405 — cache des templates compilés
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

LOGGING["root"]["level"] = "WARNING"  # noqa: F405
