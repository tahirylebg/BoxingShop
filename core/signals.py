from django.db.models.signals import m2m_changed, post_delete, post_save

from .cache import bump_catalog_version

WATCHED = [
    "catalog.Discipline", "catalog.Category", "catalog.Product", "catalog.Variant", "catalog.ProductImage",
    "catalog.Review", "catalog.SizeChart", "catalog.SizeChartRow", "content.Guide", "core.ShippingSettings",
    "core.PageMeta",
]


def connect():
    from django.apps import apps

    for label in WATCHED:
        model = apps.get_model(label)
        post_save.connect(bump_catalog_version, sender=model, dispatch_uid=f"bump-save-{label}")
        post_delete.connect(bump_catalog_version, sender=model, dispatch_uid=f"bump-del-{label}")
    m2m_changed.connect(bump_catalog_version, dispatch_uid="bump-m2m")
