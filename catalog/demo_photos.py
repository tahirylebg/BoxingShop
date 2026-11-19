"""Affectation des photos de démonstration (media/demo/credits.json) aux contenus du seed.

Chaque liste est un ordre de préférence : la première photo disponible est retenue, ce qui permet au seed de
fonctionner avec ou sans les photos Unsplash (clé API facultative). Sans aucune photo, le visuel de secours
illustré (catalog/demo_art.py) est utilisé.
"""

HERO = ["px-ring-nb", "ring-noir-blanc", "px-garde-nb", "px-combat-nb", "silhouette-salle"]

DISCIPLINES = {
    "boxe-anglaise": ["px-combat-nb", "px-arbitre-nb", "px-sparring", "px-coup-gants"],
    "muay-thai-kickboxing": ["muay-thai-kick", "kick-sac", "short-orange", "px-sac-entrainement"],
    "mma-grappling": ["mma-sac", "gants-noir-rouge", "px-boxe-salle", "px-garde-bandes"],
    "jiu-jitsu-bresilien": ["jjb-kimono", "px-jjb", "px-kimono"],
    "entrainement-sacs-de-frappe": ["sacs-alignes", "silhouette-salle", "px-sac-homme", "px-sac-repos"],
}

# Bandes plein écran (traitées en noir et blanc) : page Guides et bande campagne.
GUIDES_HERO = ["px-garde-nb", "px-sparring", "px-boxe-salle"]
CAMPAIGN = ["px-sparring", "px-boxe-salle", "px-garde-nb"]

GUIDES = {
    "choisir-poids-gants-oz": ["px-gants-gros-plan", "gants-noirs", "px-gants-salle"],
    "entretien-du-cuir": ["px-gants-cuir", "px-gants-detail", "px-gants-blancs"],
    "choisir-protege-tibias": ["kick-sac", "px-shadow"],
    "poser-ses-bandes-de-boxe": ["px-bandages-pose", "px-garde-bandes", "px-bandages-frappe"],
    "choisir-kimono-jjb": ["px-kimono", "px-jjb"],
    "choisir-sac-de-frappe": ["px-sac-entrainement", "px-sac-homme", "px-sac-repos"],
}

# Photos par forme de produit : la 1re sert de visuel principal, la suivante de 2ᵉ photo (survol des cartes).
# Le décalage par produit (rotation) évite que deux produits voisins affichent la même photo.
SHAPES = {
    "glove": ["px-gants-gros-plan", "px-gants-rouges", "px-gants-salle", "px-gants-blancs", "px-gants-detail",
              "px-coup-gants", "gants-noirs", "gants-groupe"],
    "glove_laced": ["px-gants-cuir", "px-combat-nb", "px-gants-rouges"],
    "mma_glove": ["px-garde-bandes", "px-boxe-salle", "mma-sac", "gants-noir-rouge"],
    "headgear": ["px-sparring", "casque-reglage", "px-combat-nb"],
    "headgear_bar": ["px-sparring", "casque-reglage", "px-garde-nb"],
    "mouthguard": ["px-garde-nb", "px-sparring", "px-arbitre-nb"],
    "cup": ["px-arbitre-nb", "px-ring-nb"],
    "shorts": ["px-combat-nb", "short-orange", "px-arbitre-nb", "px-sac-entrainement"],
    "shin": ["kick-sac", "muay-thai-kick", "px-sac-entrainement"],
    "pads": ["px-boxe-salle", "gants-groupe", "px-sac-homme"],
    "rashguard": ["px-garde-bandes", "px-shadow", "px-jjb"],
    "kimono": ["px-jjb", "px-kimono", "jjb-kimono"],
    "bag": ["silhouette-salle", "px-sac-homme", "px-sac-entrainement", "px-sac-repos", "sacs-alignes"],
    "rope": ["corde-salle", "px-shadow", "px-boxe-salle"],
    "wraps": ["px-bandages-pose", "px-bandages-frappe", "px-shadow", "bandages-pose"],
    "tin": ["px-gants-cuir", "px-gants-detail"],
    "bottle": ["px-gants-salle", "px-gants-detail"],
}


def pick(keys, available, offset=0, count=1):
    """Retourne jusqu'à `count` clés disponibles, en commençant au rang `offset` (rotation)."""
    present = [k for k in keys if k in available]
    if not present:
        return []
    start = offset % len(present)
    rotated = present[start:] + present[:start]
    return rotated[:count]
