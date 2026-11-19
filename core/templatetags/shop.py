import json
import re
from decimal import ROUND_HALF_UP, Decimal

from django import template
from django.core.files.storage import default_storage
from django.utils.html import conditional_escape, escape, format_html, format_html_join
from django.utils.safestring import mark_safe

register = template.Library()

_JSON_ESCAPES = {ord(">"): "\\u003E", ord("<"): "\\u003C", ord("&"): "\\u0026"}


@register.filter
def money(value):
    """12345.5 -> « 12 345,50 € » (espace fine insécable)."""
    if value in (None, ""):
        return ""
    value = Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    integer, _, cents = f"{value:.2f}".partition(".")
    sign = "-" if integer.startswith("-") else ""
    integer = integer.lstrip("-")
    groups = []
    while integer:
        groups.insert(0, integer[-3:])
        integer = integer[:-3]
    return f"{sign}{' '.join(groups)},{cents} €"


@register.simple_tag
def jsonld(data):
    """Sérialise un dict en <script type="application/ld+json"> en échappant <, > et &."""
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).translate(_JSON_ESCAPES)
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')  # contenu échappé ci-dessus


def _anchor(title):
    from django.utils.text import slugify

    import html

    return "s-" + slugify(html.unescape(str(title)).replace("**", ""))[:60]


@register.filter
def markup_toc(text):
    """Intertitres « ## » d'un contenu simple_markup : [(ancre, titre)] pour le sommaire."""
    return [(_anchor(line.strip()[3:]), line.strip()[3:].replace("**", ""))
            for line in str(text or "").splitlines() if line.strip().startswith("## ")]


@register.filter
def emphasize(text, words):
    """Met en valeur des mots-clés d'un texte saisi en back-office : échappé d'abord, puis balisé."""
    out = str(conditional_escape(text or ""))
    for w in [w.strip() for w in str(words).split(",") if w.strip()]:
        out = re.sub(rf"\b({re.escape(w)})\b", r"<em>\1</em>", out, count=1)
    return mark_safe(out)


@register.filter
def checked_count(options):
    """Nombre d'options cochées dans un groupe de filtres [(valeur, libellé, n, coché)]."""
    return sum(1 for o in options if o[3])


@register.filter
def title_split(text):
    """« Boxe anglaise » -> ("Boxe", "anglaise") : le dernier mot est mis en valeur dans les héros."""
    words = str(text or "").split()
    return (" ".join(words[:-1]), words[-1]) if len(words) > 1 else ("", words[0] if words else "")


def _inline(text):
    """Texte déjà échappé → applique uniquement **gras**."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


@register.filter(is_safe=True)
def simple_markup(text):
    """Mise en forme minimaliste et sûre : tout est échappé, puis ## intertitres, - listes, **gras**.

    Aucune balise HTML saisie n'est interprétée : pas de risque XSS.
    """
    blocks = re.split(r"\n\s*\n", str(text or "").strip())
    out = []
    for block in blocks:
        lines = [escape(line.strip()) for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if lines[0].startswith("## "):
            out.append(f'<h2 id="{_anchor(lines[0][3:])}">{_inline(lines[0][3:])}</h2>')
            lines = lines[1:]
            if not lines:
                continue
        if all(line.startswith("- ") for line in lines):
            items = "".join(f"<li>{_inline(line[2:])}</li>" for line in lines)
            out.append(f"<ul>{items}</ul>")
        else:
            out.append(f"<p>{_inline('<br>'.join(lines))}</p>")
    return mark_safe("\n".join(out))


@register.simple_tag
def responsive_img(image, sizes="100vw", loading="lazy", css_class="", alt=None, fetchpriority=None):
    """<img> WebP avec srcset à partir des déclinaisons générées par catalog.images."""
    if not image or not image.renditions:
        return ""
    widths = sorted(int(w) for w in image.renditions)
    srcset = ", ".join(f"{default_storage.url(image.renditions[str(w)])} {w}w" for w in widths)
    default = default_storage.url(image.renditions[str(widths[min(1, len(widths) - 1)])])
    height = round(image.height * 1000 / image.width) if image.width else 1000
    attrs = {
        "src": default, "srcset": srcset, "sizes": sizes, "width": 1000, "height": height,
        "alt": image.alt if alt is None else alt, "loading": loading, "decoding": "async",
    }
    if css_class:
        attrs["class"] = css_class
    if fetchpriority:
        attrs["fetchpriority"] = fetchpriority
    return format_html("<img {}>", format_html_join(" ", '{}="{}"', attrs.items()))


@register.simple_tag
def largest_rendition_url(image):
    if not image or not image.renditions:
        return ""
    return default_storage.url(image.renditions[str(max(int(w) for w in image.renditions))])


@register.simple_tag(takes_context=True)
def query_replace(context, **kwargs):
    """Reconstruit la query-string courante en remplaçant/supprimant certaines clés (pagination, tri)."""
    query = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value in (None, ""):
            query.pop(key, None)
        else:
            query[key] = value
    encoded = query.urlencode()
    return f"?{encoded}" if encoded else "?"


@register.filter
def stars(value):
    try:
        n = round(float(value))
    except (TypeError, ValueError):
        return ""
    return "★" * n + "☆" * (5 - n)


@register.simple_tag
def swatch(hex_color):
    """Pastille couleur en SVG (attribut fill) : compatible CSP sans style inline."""
    color = hex_color if re.fullmatch(r"#[0-9A-Fa-f]{6}", hex_color or "") else "#0D0D0D"
    return format_html('<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false">'
                       '<rect x="0.5" y="0.5" width="31" height="31" fill="{}"/></svg>', conditional_escape(color))
