"""Images : déclinaisons WebP multi-tailles (srcset) et traitement éditorial des photos.

Les noms de fichiers contiennent une empreinte du contenu source : ils peuvent être servis avec un cache
« immutable » d'un an (cf. deploy/nginx.conf) sans risque d'afficher une ancienne image.
Tout modèle exposant `image`, `RENDITION_WIDTHS`, `width`, `height`, `renditions` et `rendition_folder()`
est pris en charge (ProductImage, core.Photo).
"""
import hashlib
import random
from io import BytesIO
from pathlib import PurePosixPath

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageChops, ImageEnhance, ImageOps

WEBP_QUALITY = 80


def build_renditions(obj):
    """Crée une version WebP par largeur de obj.RENDITION_WIDTHS (sans agrandir la source)."""
    src = obj.image
    previous = set((obj.renditions or {}).values())
    src.open("rb")
    digest = hashlib.sha256(src.read()).hexdigest()[:10]
    src.seek(0)
    try:
        with Image.open(src) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
            obj.width, obj.height = img.size
            stem = PurePosixPath(src.name).stem
            renditions = {}
            widths = [w for w in obj.RENDITION_WIDTHS if w < img.width] + [min(img.width, max(obj.RENDITION_WIDTHS))]
            for width in sorted(set(widths)):
                height = round(img.height * width / img.width)
                resized = img.resize((width, height), Image.Resampling.LANCZOS) if width != img.width else img
                buffer = BytesIO()
                resized.save(buffer, "WEBP", quality=WEBP_QUALITY, method=6)
                path = f"{obj.rendition_folder()}/{stem}-{digest}-{width}.webp"
                if default_storage.exists(path):
                    default_storage.delete(path)
                renditions[str(width)] = default_storage.save(path, ContentFile(buffer.getvalue()))
    finally:
        src.close()
    for old in previous - set(renditions.values()):
        if default_storage.exists(old):
            default_storage.delete(old)
    obj.renditions = renditions
    return renditions


def _overlay(base, noise):
    """Grain : décale chaque pixel de (bruit - 128), bruit gaussien monochrome centré sur 128."""
    return ImageChops.add(base, noise, scale=1.0, offset=-128)


def treat_photo(data, *, mode="editorial", max_width=2000, crop=None, seed=0):
    """Unifie l'ambiance des photos (au seed) et renvoie un JPEG.

    - editorial : légère désaturation + contraste, pour les fiches et vignettes ;
    - bw : noir et blanc contrasté + grain, pour le hero ;
    crop : ratio largeur/hauteur à imposer (recadrage centré), ex. 1.0 pour un carré.
    """
    with Image.open(BytesIO(data)) as src:
        img = ImageOps.exif_transpose(src).convert("RGB")
    if crop:
        img = ImageOps.fit(img, _fit_size(img, crop), Image.Resampling.LANCZOS, centering=(0.5, 0.42))
    if img.width > max_width:
        img = img.resize((max_width, round(img.height * max_width / img.width)), Image.Resampling.LANCZOS)
    if mode == "product":
        pass  # photo produit : couleurs fidèles, aucun traitement colorimétrique
    elif mode == "bw":
        img = ImageOps.grayscale(img)
        img = ImageOps.autocontrast(img, cutoff=1)
        img = ImageEnhance.Contrast(img).enhance(1.25).convert("RGB")
        img = _overlay(img, Image.merge("RGB", [_noise(img.size, 22, seed)] * 3))
    else:
        img = ImageEnhance.Color(img).enhance(0.72)
        img = ImageEnhance.Contrast(img).enhance(1.12)
        img = _overlay(img, Image.merge("RGB", [_noise(img.size, 7, seed)] * 3))
    out = BytesIO()
    img.save(out, "JPEG", quality=88, optimize=True, progressive=True)
    return out.getvalue()


def _noise(size, strength, seed):
    """Bruit gaussien déterministe (même seed → même grain, seed reproductible)."""
    rng = random.Random(seed)
    noise = Image.effect_noise(size, strength)
    return noise.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if rng.random() < 0.5 else noise


def _fit_size(img, ratio):
    if img.width / img.height > ratio:
        return round(img.height * ratio), img.height
    return img.width, round(img.width / ratio)
