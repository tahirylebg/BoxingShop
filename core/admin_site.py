from datetime import timedelta

from django.contrib import admin
from django.db.models import Count, Sum
from django.utils import timezone


class BoxingAdminSite(admin.AdminSite):
    site_header = "Boxing Shop — Back-office"
    site_title = "Boxing Shop admin"
    index_title = "Tableau de bord"
    index_template = "admin/boxing_index.html"

    def index(self, request, extra_context=None):
        from accounts.models import Customer
        from catalog.models import Variant
        from orders.models import Order

        since = timezone.now() - timedelta(days=30)
        paid_statuses = [Order.Status.PAID, Order.Status.PREPARING, Order.Status.SHIPPED, Order.Status.DELIVERED]
        sales = Order.objects.filter(status__in=paid_statuses, paid_at__gte=since).aggregate(
            revenue=Sum("total"), count=Count("id"))
        extra_context = {
            **(extra_context or {}),
            "low_stock": Variant.objects.low_stock().select_related("product").order_by("stock", "product__name")[:25],
            "low_stock_count": Variant.objects.low_stock().count(),
            "to_prepare": Order.objects.filter(status__in=[Order.Status.PAID, Order.Status.PREPARING]).count(),
            "stock_issues": Order.objects.filter(stock_issue=True, created_at__gte=since).count(),
            "club_requests": Customer.objects.filter(club_status=Customer.ClubStatus.PENDING).count(),
            "revenue_30d": sales["revenue"] or 0,
            "orders_30d": sales["count"],
        }
        return super().index(request, extra_context)
