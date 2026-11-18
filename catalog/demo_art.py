"""Génère des visuels produits de démonstration (silhouette « détourée » sur fond béton clair avec grain).

Utilisé uniquement par `manage.py seed_demo` : en production, les visuels sont des photos uploadées
depuis l'admin et converties automatiquement en WebP (catalog.images).
"""
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

ASSETS = Path(__file__).parent / "demo_assets"
SIZE = 1200
SS = 2  # suréchantillonnage pour l'anticrénelage
INK = (13, 13, 13)
CONCRETE = (229, 227, 220)


def _hex(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _shade(rgb, factor):
    if max(rgb) < 40:  # teintes très sombres : on éclaircit au lieu de multiplier
        return tuple(min(255, int(c + 60 * (factor - 0.5))) for c in rgb)
    return tuple(max(0, min(255, int(c * factor))) for c in rgb)


class _Pen:
    """Dessine dans un repère 0–1000 mis à l'échelle de la toile suréchantillonnée."""

    def __init__(self, draw, fill, stroke=INK):
        self.d, self.fill, self.stroke = draw, fill, stroke
        self.k = SIZE * SS / 1000
        self.w = int(7 * SS)

    def _box(self, box):
        return [v * self.k for v in box]

    def ellipse(self, box, fill=None):
        self.d.ellipse(self._box(box), fill=fill or self.fill, outline=self.stroke, width=self.w)

    def rect(self, box, r=40, fill=None):
        self.d.rounded_rectangle(self._box(box), radius=r * self.k, fill=fill or self.fill, outline=self.stroke,
                                 width=self.w)

    def poly(self, pts, fill=None):
        self.d.polygon([(x * self.k, y * self.k) for x, y in pts], fill=fill or self.fill, outline=self.stroke,
                       width=self.w)

    def line(self, pts, width=7, fill=None):
        self.d.line([(x * self.k, y * self.k) for x, y in pts], fill=fill or self.stroke, width=int(width * SS),
                    joint="curve")

    def arc(self, box, start, end, width=7, fill=None):
        self.d.arc(self._box(box), start, end, fill=fill or self.stroke, width=int(width * SS))


def _glove(p, c, laced=False):
    p.rect((330, 600, 690, 880), r=30, fill=_shade(c, 0.85))
    p.line([(345, 700), (675, 700)], width=5, fill=_shade(c, 1.25))
    p.ellipse((290, 170, 740, 700))
    p.ellipse((200, 360, 400, 640))
    p.arc((330, 230, 700, 560), 200, 340, width=6, fill=_shade(c, 0.6))
    if laced:
        for y in range(620, 860, 50):
            p.line([(470, y), (550, y + 25)], width=6, fill=(244, 243, 239))
            p.line([(550, y), (470, y + 25)], width=6, fill=(244, 243, 239))


def _mma_glove(p, c):
    p.rect((330, 560, 690, 830), r=30, fill=_shade(c, 0.85))
    p.rect((300, 250, 720, 600), r=110)
    p.ellipse((230, 400, 380, 580))
    for x in (390, 480, 570):
        p.line([(x, 260), (x, 360)], width=6, fill=_shade(c, 0.55))


def _shin(p, c):
    p.rect((360, 120, 640, 800), r=120)
    p.rect((380, 770, 620, 900), r=60, fill=_shade(c, 0.85))
    for y in (300, 560):
        p.rect((330, y, 670, y + 60), r=10, fill=INK)
    p.line([(500, 160), (500, 760)], width=5, fill=_shade(c, 0.6))


def _headgear(p, c, bar=False):
    p.ellipse((260, 150, 740, 790))
    p.ellipse((360, 360, 640, 660), fill=CONCRETE)
    p.rect((300, 640, 700, 760), r=60, fill=_shade(c, 0.85))
    if bar:
        p.rect((340, 560, 660, 620), r=20, fill=INK)
    p.arc((290, 180, 710, 520), 200, 340, width=6, fill=_shade(c, 0.6))


def _mouthguard(p, c):
    p.arc((250, 300, 750, 800), 180, 360, width=120, fill=INK)
    p.arc((262, 312, 738, 788), 180, 360, width=96, fill=c)


def _cup(p, c):
    p.rect((220, 330, 780, 400), r=20, fill=INK)
    p.poly([(330, 400), (670, 400), (600, 720), (500, 790), (400, 720)])


def _shorts(p, c):
    p.rect((280, 220, 720, 320), r=12, fill=INK)
    p.poly([(290, 320), (710, 320), (780, 790), (530, 790), (500, 560), (470, 790), (220, 790)])
    p.line([(250, 560), (260, 780)], width=18, fill=_shade(c, 1.6) if sum(c) < 200 else INK)


def _top(p, c, kimono=False):
    p.poly([(330, 180), (430, 150), (570, 150), (670, 180), (820, 330), (740, 420), (680, 370), (680, 850),
            (320, 850), (320, 370), (260, 420), (180, 330)])
    if kimono:
        p.line([(430, 150), (520, 450), (640, 170)], width=10)
        p.rect((320, 560, 680, 610), r=6, fill=INK)
    else:
        p.line([(320, 600), (680, 600)], width=5, fill=_shade(c, 0.6))


def _wraps(p, c):
    p.rect((180, 520, 760, 610), r=10, fill=_shade(c, 0.9))
    p.ellipse((520, 300, 840, 620))
    p.ellipse((630, 410, 730, 510), fill=_shade(c, 0.7))


def _bag(p, c):
    p.line([(500, 60), (500, 140)], width=10)
    p.line([(500, 140), (380, 230)], width=8)
    p.line([(500, 140), (620, 230)], width=8)
    p.rect((350, 220, 650, 920), r=50)
    for y in (330, 810):
        p.line([(355, y), (645, y)], width=6, fill=_shade(c, 0.6))


def _pads(p, c):
    p.ellipse((170, 280, 520, 720))
    p.ellipse((480, 280, 830, 720), fill=_shade(c, 0.9))
    p.ellipse((280, 400, 410, 600), fill=(244, 243, 239))
    p.ellipse((590, 400, 720, 600), fill=(244, 243, 239))


def _rope(p, c):
    p.arc((200, 150, 800, 900), 200, 340, width=10)
    p.rect((150, 470, 230, 760), r=30)
    p.rect((770, 470, 850, 760), r=30)


def _tin(p, c):
    p.rect((300, 420, 700, 760), r=20)
    p.ellipse((300, 360, 700, 480), fill=_shade(c, 1.2))
    p.rect((300, 560, 700, 620), r=0, fill=INK)


def _bottle(p, c):
    p.rect((420, 180, 580, 290), r=10, fill=INK)
    p.rect((360, 280, 640, 860), r=60)
    p.rect((360, 480, 640, 640), r=0, fill=(244, 243, 239))


SHAPES = {
    "glove": _glove,
    "glove_laced": lambda p, c: _glove(p, c, laced=True),
    "mma_glove": _mma_glove,
    "shin": _shin,
    "headgear": _headgear,
    "headgear_bar": lambda p, c: _headgear(p, c, bar=True),
    "mouthguard": _mouthguard,
    "cup": _cup,
    "shorts": _shorts,
    "rashguard": _top,
    "kimono": lambda p, c: _top(p, c, kimono=True),
    "wraps": _wraps,
    "bag": _bag,
    "pads": _pads,
    "rope": _rope,
    "tin": _tin,
    "bottle": _bottle,
}


def render(shape, color_hex, caption):
    """Retourne les octets PNG d'un visuel 1200×1200."""
    big = Image.new("RGB", (SIZE * SS, SIZE * SS), CONCRETE)
    draw = ImageDraw.Draw(big)
    rgb = _hex(color_hex)
    dark = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) < 60
    SHAPES[shape](_Pen(draw, rgb, stroke=(110, 108, 102) if dark else INK), rgb)
    img = big.resize((SIZE, SIZE), Image.Resampling.LANCZOS)

    # Grain photographique contrasté (léger)
    noise = Image.effect_noise((SIZE, SIZE), 28).convert("RGB")
    img = ImageChops.blend(img, ImageChops.multiply(img, noise.point(lambda v: 200 + v // 4)), 0.35)

    draw = ImageDraw.Draw(img)
    mono = ImageFont.truetype(str(ASSETS / "JetBrainsMono-Bold.ttf"), 26)
    draw.line([(48, SIZE - 96), (SIZE - 48, SIZE - 96)], fill=INK, width=2)
    draw.text((48, SIZE - 80), caption.upper(), font=mono, fill=INK)
    draw.text((SIZE - 48, SIZE - 80), "BOXING SHOP", font=mono, fill=INK, anchor="ra")

    out = BytesIO()
    img.save(out, "PNG", optimize=True)
    return out.getvalue()
