from django.core.files.storage import default_storage
from django.db.models.signals import post_delete
from django.dispatch import receiver

from core.models import Photo

from .models import ProductImage


@receiver(post_delete, sender=ProductImage)
@receiver(post_delete, sender=Photo)
def delete_image_files(sender, instance, **kwargs):
    """Supprime l'image source et ses déclinaisons WebP quand l'image est retirée."""
    paths = [instance.image.name, *(instance.renditions or {}).values()]
    for path in filter(None, paths):
        if default_storage.exists(path):
            default_storage.delete(path)
