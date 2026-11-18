from django.conf import settings


class SecurityHeadersMiddleware:
    """Ajoute la Content-Security-Policy et quelques en-têtes de durcissement."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.policy = self._build(settings.CSP_POLICY)
        admin_policy = {**settings.CSP_POLICY, **settings.CSP_ADMIN_OVERRIDES}
        self.admin_policy = self._build(admin_policy)

    @staticmethod
    def _build(policy):
        return "; ".join(f"{k} {' '.join(v)}" for k, v in policy.items())

    def __call__(self, request):
        response = self.get_response(request)
        is_admin = request.path.startswith("/admin/")
        response.setdefault("Content-Security-Policy", self.admin_policy if is_admin else self.policy)
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=(self)")
        response.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        return response
