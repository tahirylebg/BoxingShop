"""Télécharge les photos de démonstration libres de droits dans media/demo/ et consigne leurs crédits.

    python scripts/fetch_photos.py            # télécharge ce qui manque
    python scripts/fetch_photos.py --force    # retélécharge tout

Sources : Pexels (licence Pexels) et Unsplash (licence Unsplash) — usage commercial autorisé, sans attribution
obligatoire ; nous créditons tout de même chaque auteur (CREDITS.md + légende discrète sur le site).

- Pexels : CDN public, sans clé. Le nom de l'auteur est complété via l'API officielle si PEXELS_API_KEY est défini
  (sinon : auteur connu indiqué ci-dessous, ou « Contributeur Pexels » avec le lien vers la photo).
- Unsplash : uniquement via l'API officielle (UNSPLASH_ACCESS_KEY, https://unsplash.com/developers), qui fournit
  l'auteur et déclenche le suivi de téléchargement exigé par Unsplash. Sans clé, ces photos sont ignorées.

Chaque fichier est vérifié (HTTP 200, type image, ouverture Pillow, largeur minimale). Une photo indisponible est
ignorée : `seed_demo` la remplace par un visuel de secours stylé. Les traitements (désaturation, contraste, N&B)
sont appliqués au seed : les originaux restent intacts.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "media" / "demo" / "originals"
CREDITS_JSON = ROOT / "media" / "demo" / "credits.json"
CREDITS_MD = ROOT / "CREDITS.md"
MIN_WIDTH = 1000
UA = "BoxingShopDemoFetcher/1.0"

# (clé, source, identifiant, texte alternatif, auteur connu ou None)
PHOTOS = [
    # Noir & blanc, ring
    ("px-ring-nb", "pexels", "8745632", "Boxeur dans le ring d'une salle industrielle, serviette à la main", "Ron Lach"),
    ("px-combat-nb", "pexels", "2691309", "Deux boxeurs en plein combat, photographie noir et blanc", "David Guerrero"),
    ("px-garde-nb", "pexels", "30323312", "Boxeur en garde à l'entraînement, noir et blanc", "Amirr Zolfaghari"),
    ("px-sparring", "pexels", "17802683", "Deux boxeurs à l'entraînement sur le ring", "David Kwewum"),
    ("px-arbitre-nb", "pexels", "3797", "Arbitre levant le bras d'un boxeur dans le ring", "ClickerHappy"),
    # Gants
    ("px-gants-gros-plan", "pexels", "6296121", "Gros plan sur des gants de boxe suspendus", None),
    ("px-gants-salle", "pexels", "6296107", "Gants de boxe dans une salle d'entraînement", None),
    ("px-gants-blancs", "pexels", "6296062", "Gants de boxe blancs en gros plan", None),
    ("px-gants-cuir", "pexels", "6739945", "Paire de gants de boxe en cuir brun", None),
    ("px-gants-rouges", "pexels", "10689272", "Gants de boxe rouges suspendus", None),
    ("px-gants-detail", "pexels", "7991941", "Gants de boxe en gros plan", None),
    ("px-coup-gants", "pexels", "9944908", "Boxeur portant un direct, gants aux mains", None),
    ("gants-groupe", "pexels", "5535931", "Pratiquants portant des gants de boxe", None),
    # Bandages
    ("px-bandages-pose", "pexels", "4790417", "Boxeur posant ses bandes de main", "Anete Lusina"),
    ("px-shadow", "pexels", "6295786", "Boxeur aux mains bandées en shadow boxing", None),
    ("px-bandages-frappe", "pexels", "7289996", "Boxeur frappant, mains bandées", None),
    ("px-garde-bandes", "pexels", "14762167", "Boxeur en garde, poings levés", None),
    # Salle, sacs
    ("silhouette-salle", "pexels", "8736743", "Silhouette d'un boxeur dans une salle aux sacs suspendus", None),
    ("px-sac-entrainement", "pexels", "7991687", "Boxeur travaillant au sac de frappe", None),
    ("px-sac-homme", "pexels", "4804058", "Homme à l'entraînement de boxe au sac", None),
    ("px-boxe-salle", "pexels", "9944902", "Boxeur à l'entraînement en salle", None),
    ("px-sac-repos", "pexels", "4804262", "Boxeur appuyé contre un sac de frappe", None),
    ("kick-sac", "pexels", "7992155", "Kickboxeur frappant un sac de pied", None),
    # Grappling
    ("px-jjb", "pexels", "8611251", "Deux pratiquants de jiu-jitsu brésilien en kimono", None),
    ("px-kimono", "pexels", "7988389", "Jeune pratiquant en kimono de jiu-jitsu", None),
    # Unsplash (API officielle requise)
    ("ring-noir-blanc", "unsplash", "4zaaZR_vjnc", "Boxeur seul dans un ring, photographie noir et blanc", None),
    ("sacs-alignes", "unsplash", "2Ig4WSod3GQ", "Rangée de sacs de frappe suspendus dans une salle", None),
    ("gants-noirs", "unsplash", "XmvuWRDimrg", "Paire de gants de boxe noirs", None),
    ("gants-noir-rouge", "unsplash", "CcJpFWrXlb8", "Combattant portant des gants noir et rouge sur un tatami", None),
    ("muay-thai-kick", "unsplash", "h8sl-oNcat0", "Combattant de muay thaï portant un coup de pied", None),
    ("short-orange", "unsplash", "--kCYRH98Ng", "Combattants en short orange et gants noirs", None),
    ("casque-reglage", "unsplash", "vuZi5zk5W-A", "Entraîneur ajustant le casque d'un boxeur dans le ring", None),
    ("bandages-pose", "unsplash", "qxYDhV0rBPk", "Pose de bandages sur les mains d'une boxeuse", None),
    ("mma-sac", "unsplash", "nHDTLmC2kXQ", "Combattant de MMA frappant un sac blanc", None),
    ("jjb-kimono", "unsplash", "GeRXOhXA548", "Pratiquant en kimono de jiu-jitsu brésilien", None),
    ("corde-salle", "unsplash", "d5Q4aBfZclM", "Sportive sautant à la corde dans une salle", None),
]


class Skipped(Exception):
    pass


def _get(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def _unsplash(photo_id):
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not key:
        raise Skipped("UNSPLASH_ACCESS_KEY absent")
    auth = {"Authorization": f"Client-ID {key}", "Accept-Version": "v1"}
    info = json.loads(_get(f"https://api.unsplash.com/photos/{photo_id}", auth)[0])
    _get(info["links"]["download_location"], auth)  # suivi de téléchargement exigé par Unsplash
    data, ctype = _get(f"{info['urls']['raw']}&w=2000&fm=jpg&q=85")
    page = f"{info['links']['html']}?utm_source=boxing_shop&utm_medium=referral"
    return data, ctype, info["user"]["name"], page


def _pexels(photo_id, known_author):
    data, ctype = _get(f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg"
                       "?auto=compress&cs=tinysrgb&w=2000")
    author, page = known_author or "Contributeur Pexels", f"https://www.pexels.com/photo/{photo_id}/"
    key = os.environ.get("PEXELS_API_KEY")
    if key:
        info = json.loads(_get(f"https://api.pexels.com/v1/photos/{photo_id}", {"Authorization": key})[0])
        author, page = info.get("photographer") or author, info.get("url") or page
    return data, ctype, author, page


def fetch(entry):
    key, source, pid, alt, known_author = entry
    if source == "unsplash":
        data, ctype, author, page = _unsplash(pid)
    else:
        data, ctype, author, page = _pexels(pid, known_author)
    if not ctype.startswith("image/"):
        raise ValueError(f"type inattendu {ctype}")
    with Image.open(BytesIO(data)) as img:
        img.verify()
    with Image.open(BytesIO(data)) as img:
        if img.width < MIN_WIDTH:
            raise ValueError(f"largeur insuffisante ({img.width}px)")
        size = img.size
    (OUT / f"{key}.jpg").write_bytes(data)
    return {"key": key, "file": f"demo/originals/{key}.jpg", "source": source.capitalize(), "id": pid,
            "author": author, "page": page, "license": f"Licence {source.capitalize()}", "alt": alt,
            "size": list(size)}


def main(force=False):
    OUT.mkdir(parents=True, exist_ok=True)
    previous = {c["key"]: c for c in json.loads(CREDITS_JSON.read_text("utf-8"))} if CREDITS_JSON.exists() else {}
    credits, failures, skipped = [], [], []
    for entry in PHOTOS:
        key = entry[0]
        if not force and key in previous and (OUT / f"{key}.jpg").exists():
            credits.append(previous[key])
            continue
        try:
            credits.append(fetch(entry))
            print(f"OK    {key}")
        except Skipped:
            skipped.append(key)
        except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
            failures.append(key)
            print(f"ÉCHEC {key} : {exc}", file=sys.stderr)
    CREDITS_JSON.write_text(json.dumps(credits, ensure_ascii=False, indent=2), "utf-8")
    write_credits_md(credits)
    print(f"{len(credits)} photos disponibles, {len(failures)} échec(s)"
          f"{' : ' + ', '.join(failures) if failures else ''}")
    if skipped:
        print(f"{len(skipped)} photo(s) Unsplash ignorée(s) : définissez UNSPLASH_ACCESS_KEY pour les télécharger.")
    return 0


def write_credits_md(credits):
    lines = [
        "# Crédits photographiques",
        "",
        "Photos de démonstration téléchargées par `scripts/fetch_photos.py`, utilisées sous la",
        "[licence Pexels](https://www.pexels.com/license/) ou la [licence Unsplash](https://unsplash.com/license) :",
        "usage commercial autorisé, sans attribution obligatoire. Nous créditons néanmoins chaque auteur.",
        "Traitement appliqué au seed : légère désaturation et contraste (photo d'accueil en noir et blanc granuleux).",
        "Les photos illustrent l'univers de la boutique ; elles ne représentent pas nécessairement le produit exact.",
        "",
        "| Fichier | Sujet | Auteur | Source |",
        "|---|---|---|---|",
    ]
    lines += [f"| `{c['key']}` | {c['alt']} | {c['author']} | [{c['source']}]({c['page']}) |" for c in credits]
    CREDITS_MD.write_text("\n".join(lines) + "\n", "utf-8")


if __name__ == "__main__":
    sys.exit(main(force="--force" in sys.argv))
