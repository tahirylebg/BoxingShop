"""Couleurs du catalogue : nom canonique (celui des variantes), slug d'URL, teinte et formes grammaticales.

La couleur est une clé texte partagée par Variant.color et ProductImage.color (pas de table dédiée).
"""
import re
import unicodedata

from django.utils.text import slugify

# nom canonique -> (teinte de pastille, formes reconnues dans une recherche : genre et nombre)
COLORS = {
    "Noir": ("#0D0D0D", ("noir", "noire", "noirs", "noires")),
    "Blanc": ("#F4F3EF", ("blanc", "blanche", "blancs", "blanches")),
    "Rouge": ("#C81E1E", ("rouge", "rouges")),
    "Bleu": ("#1F3F99", ("bleu", "bleue", "bleus", "bleues")),
    "Kaki": ("#5B5B3A", ("kaki", "kakis")),
    "Fauve": ("#8B5A2B", ("fauve", "fauves", "marron", "marrons", "brun", "brune", "bruns", "brunes")),
}


def _fold(text):
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode()
    return text.lower()


_FORMS = {form: name for name, (_, forms) in COLORS.items() for form in forms}


def color_slug(name):
    return slugify(name or "")


def from_slug(value):
    """« bleu », « Bleu », « bleue » -> « Bleu » (None si inconnu)."""
    folded = _fold(value).strip()
    return next((name for name in COLORS if color_slug(name) == folded), None) or _FORMS.get(folded)


def color_hex(name):
    return COLORS.get(name, ("#0D0D0D", ()))[0]


def split_query(query):
    """« gants bleus » -> (« gants », ["Bleu"]) : extrait les couleurs d'une recherche texte."""
    found, kept = [], []
    for word in re.split(r"\s+", (query or "").strip()):
        name = _FORMS.get(_fold(word))
        if name:
            if name not in found:
                found.append(name)
        elif word:
            kept.append(word)
    return " ".join(kept), found


def singular(word):
    """Singulier approximatif pour la recherche : « gants » -> « gant », « bandes » -> « bande »."""
    w = word.lower()
    if len(w) > 3 and w.endswith(("s", "x")) and not w.endswith("ss"):
        return w[:-1]
    return w
