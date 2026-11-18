"""Conversion automatique des images produits en WebP multi-tailles (srcset)."""
from io import BytesIO
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps

WEBP_QUALITY = 80


def build_renditions(product_image):
    """Crée une version WebP par largeur de ProductImage.RENDITION_WIDTHS (sans agrandir la source)."""
    src = product_image.image
    src.open("rb")
    try:
        with Image.open(src) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
            product_image.width, product_image.height = img.size
            stem = PurePosixPath(src.name).stem
            renditions = {}
            widths = [w for w in product_image.RENDITION_WIDTHS if w < img.width] + [
                min(img.width, max(product_image.RENDITION_WIDTHS))
            ]
            for width in sorted(set(widths)):
                height = round(img.height * width / img.width)
                resized = img.resize((width, height), Image.Resampling.LANCZOS) if width != img.width else img
                buffer = BytesIO()
                resized.save(buffer, "WEBP", quality=WEBP_QUALITY, method=6)
                path = f"products/webp/{product_image.product_id}/{stem}-{width}.webp"
                if default_storage.exists(path):
                    default_storage.delete(path)
                renditions[str(width)] = default_storage.save(path, ContentFile(buffer.getvalue()))
    finally:
        src.close()
    product_image.renditions = renditions
    return renditions
