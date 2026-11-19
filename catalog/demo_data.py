"""Jeu de données de démonstration (utilisé par `manage.py seed_demo`)."""

DISCIPLINES = [
    ("boxe-anglaise", "Boxe anglaise", "Boxe", "Le noble art : gants, casques et tenues de ring.",
     "Du premier sac au combat officiel, l'équipement du boxeur anglais doit protéger les mains et respecter la "
     "règle. Gants lacés ou à scratch, casques homologués, shorts de gala."),
    ("muay-thai-kickboxing", "Muay Thaï & Kickboxing", "Muay Thaï", "Huit armes, une exigence : protéger tibias, coudes et mains.",
     "Gants à manchette longue pour le clinch, protège-tibias cuir et shorts traditionnels pour les disciplines "
     "pieds-poings."),
    ("mma-grappling", "MMA & Grappling", "MMA", "Frapper, projeter, soumettre : un matériel polyvalent.",
     "Gants à doigts ouverts, rashguards de compression et shorts hybrides pensés pour la cage et le sol."),
    ("jiu-jitsu-bresilien", "Jiu-Jitsu Brésilien", "JJB", "Kimonos tissés et rashguards pour le tatami.",
     "Des kimonos à la trame robuste, conformes aux règles IBJJF, et des tenues No-Gi qui résistent aux saisies."),
    ("entrainement-sacs-de-frappe", "Entraînement & Sacs de frappe", "Entraînement", "Le matériel de salle qui encaisse.",
     "Sacs lourds, pattes d'ours, paos et cordes à sauter : l'équipement de travail quotidien des clubs."),
]

CATEGORIES = [
    # slug, nom, parent
    ("gants", "Gants", None),
    ("protections", "Protections", None),
    ("protege-tibias", "Protège-tibias", "protections"),
    ("casques", "Casques", "protections"),
    ("protege-dents", "Protège-dents", "protections"),
    ("coquilles", "Coquilles", "protections"),
    ("tenues", "Tenues", None),
    ("shorts", "Shorts", "tenues"),
    ("kimonos", "Kimonos", "tenues"),
    ("rashguards", "Rashguards", "tenues"),
    ("bandages-soins", "Bandages & Soins", None),
    ("materiel-de-club", "Matériel de club", None),
]

SIZE_CHARTS = [
    {
        "key": "gants", "name": "Poids de gant conseillé", "category": "gants", "measure": "Poids de gant",
        "intro": "Le poids du gant (en onces) dépend de votre gabarit et de l'usage : plus le gant est lourd, plus "
                 "il protège votre partenaire en sparring.",
        "rows": [
            (None, 45, None, None, "8–10 oz", "Jeunes, sac et pattes d'ours"),
            (45, 60, None, None, "10–12 oz", "Sac : 10 oz · Sparring : 12 oz"),
            (60, 75, None, None, "12–14 oz", "Sac : 12 oz · Sparring : 14 oz"),
            (75, 90, None, None, "14–16 oz", "Sac : 14 oz · Sparring : 16 oz"),
            (90, None, None, None, "16–18 oz", "Sparring lourd : 18 oz"),
        ],
    },
    {
        "key": "tibias", "name": "Taille de protège-tibias", "category": "protege-tibias", "measure": "Taille",
        "intro": "Mesurez du dessous du genou jusqu'au cou-de-pied. En cas d'hésitation, prenez la taille au-dessus.",
        "rows": [
            (None, None, None, 165, "S", "Longueur tibia 32–35 cm"),
            (None, None, 165, 175, "M", "Longueur tibia 35–38 cm"),
            (None, None, 175, 185, "L", "Longueur tibia 38–41 cm"),
            (None, None, 185, None, "XL", "Longueur tibia > 41 cm"),
        ],
    },
    {
        "key": "tenues", "name": "Guide des tailles textiles", "category": "tenues", "measure": "Taille",
        "intro": "Coupe athlétique. Entre deux tailles, choisissez la plus grande pour les shorts de Muay Thaï.",
        "rows": [
            (45, 55, 155, 165, "XS", ""),
            (55, 65, 162, 172, "S", ""),
            (65, 75, 170, 180, "M", ""),
            (75, 85, 177, 187, "L", ""),
            (85, 95, 182, 192, "XL", ""),
            (95, None, 188, None, "XXL", ""),
        ],
    },
    {
        "key": "kimonos", "name": "Guide des tailles kimonos", "category": "kimonos", "measure": "Taille",
        "intro": "Le kimono rétrécit de 3 à 5 % au premier lavage à 30 °C : ne le lavez jamais au-delà.",
        "rows": [
            (None, 60, 160, 170, "S (A1)", ""),
            (60, 75, 168, 178, "M (A2)", ""),
            (75, 90, 176, 186, "L (A3)", ""),
            (90, 105, 184, 194, "XL (A4)", ""),
            (105, None, 192, None, "XXL (A5)", ""),
        ],
    },
    {
        "key": "mma", "name": "Taille de gants MMA", "category": None, "measure": "Taille",
        "intro": "Mesurez le tour de main à la base des doigts, pouce exclu.",
        "rows": [
            (None, None, None, None, "S", "Tour de main 17–19 cm"),
            (None, None, None, None, "M", "Tour de main 19–21 cm"),
            (None, None, None, None, "L", "Tour de main 21–23 cm"),
            (None, None, None, None, "XL", "Tour de main > 23 cm"),
        ],
    },
]

BLACK, RED, WHITE, LEATHER, BLUE, OLIVE = (
    ("Noir", "#0D0D0D"), ("Rouge", "#C81E1E"), ("Blanc", "#F4F3EF"), ("Fauve", "#B45309"), ("Bleu", "#1E3A8A"),
    ("Kaki", "#4D5A2C"),
)
OZ = [10, 12, 14, 16]

# Chaque produit : code SKU, slug, nom, discipline, autres disciplines, type, visuel, couleurs,
# poids (oz) ou tailles, prix de base, supplément par cran de poids, specs…
PRODUCTS = [
    # --- Boxe anglaise -------------------------------------------------------------------------------
    dict(code="GHC", slug="gant-cuir-heritage-pro", name="Gant Heritage Cuir Pro", disc="boxe-anglaise",
         also=["muay-thai-kickboxing", "entrainement-sacs-de-frappe"], cat="gants", shape="glove",
         colors=[BLACK, RED], weights=OZ, price=149, step=5, material="cuir", level="sparring", range="pro",
         padding="Mousse multicouche injectée 3 densités", closure="Scratch large 10 cm", origin="Cousu main, Pakistan",
         extra={"Doublure": "Microfibre respirante", "Pouce": "Attaché anti-blessure"}, featured=True, sales=412,
         low=True,
         short="Cuir pleine fleur, mousse 3 densités : le gant de sparring qui dure des saisons.",
         desc="Le Heritage Cuir Pro reprend la ligne des gants de gala des années 60 avec une construction "
              "moderne.\n\n## Construction\n- Cuir de vachette pleine fleur, tanné végétal\n- Mousse injectée "
              "trois densités, rembourrage concentré sur les phalanges\n- Pouce attaché pour limiter les "
              "blessures oculaires\n\n## Pour qui ?\nPratiquants réguliers qui alternent sac, pattes d'ours et "
              "sparring technique."),
    dict(code="GLC", slug="gant-combat-lacets-championnat", name="Gant de combat Lacets Championnat",
         disc="boxe-anglaise", cat="gants", shape="glove_laced", colors=[RED, BLACK], weights=[8, 10],
         price=189, step=0, material="cuir", level="combat", range="competition",
         padding="Crin de cheval et mousse latex", closure="Lacets cirés", origin="Cousu main, Mexique",
         extra={"Homologation": "Conforme règlement amateur"}, featured=True, sales=96,
         short="Le gant lacé de gala : compact, précis, homologué pour la compétition.",
         desc="Rembourrage crin et latex pour un toucher sec et une frappe précise.\n\n## Points clés\n- "
              "Fermeture à lacets cirés : maintien total du poignet\n- 8 oz jusqu'à 66,7 kg, 10 oz au-delà\n- "
              "Cuir pleine fleur double couture"),
    dict(code="GSM", slug="gant-sparring-microfibre", name="Gant Sparring Microfibre", disc="boxe-anglaise",
         also=["muay-thai-kickboxing"], cat="gants", shape="glove", colors=[BLACK, WHITE], weights=OZ, price=69,
         step=3, material="microfibre", level="sparring", padding="Mousse double densité", closure="Scratch",
         origin="Thaïlande", featured=True, sales=588,
         short="Microfibre haute résistance, entretien facile, prix club.",
         desc="Un gant polyvalent pour l'entraînement intensif.\n\nLa microfibre ne craquelle pas et se nettoie "
              "d'un coup d'éponge : idéal pour les séances quotidiennes."),
    dict(code="GIC", slug="gant-initiation-club", name="Gant Initiation Club", disc="boxe-anglaise",
         also=["entrainement-sacs-de-frappe"], cat="gants", shape="glove", colors=[RED, BLUE],
         weights=[8, 10, 12], price=39, step=2, material="synthetique", level="debutant", padding="Mousse moulée",
         closure="Scratch", origin="Chine", sales=640,
         short="Le premier gant : léger, robuste, idéal pour découvrir la boxe.",
         desc="Pensé pour les cours d'initiation et les salles qui équipent leurs adhérents.\n\n- Paume "
              "aérée\n- Scratch facile à fermer seul"),
    dict(code="CBO", slug="casque-ouvert-cuir", name="Casque ouvert Cuir", disc="boxe-anglaise",
         also=["muay-thai-kickboxing"], cat="casques", shape="headgear", colors=[BLACK, RED],
         sizes=["S", "M", "L", "XL"], price=119, step=0, material="cuir", level="sparring", range="pro",
         padding="Mousse anti-choc 25 mm", closure="Laçage arrière + scratch menton", origin="Pakistan",
         sales=144, short="Protection des pommettes et vision dégagée pour le sparring.",
         desc="Casque ouvert à joues protégées.\n\n## Réglage\nLaçage arrière pour ajuster le tour de tête au "
              "millimètre, mentonnière à scratch."),
    dict(code="CBB", slug="casque-barre-sparring", name="Casque à barre Sparring", disc="boxe-anglaise",
         cat="casques", shape="headgear_bar", colors=[BLACK], sizes=["M", "L", "XL"], price=159, step=0,
         material="cuir", level="sparring", range="competition", padding="Mousse 30 mm + barre nasale",
         closure="Laçage arrière", origin="Pakistan", sales=61, low=True,
         short="Barre frontale : le nez et la bouche à l'abri en sparring dur.",
         desc="La barre absorbe les coups directs au visage : le choix des boxeurs lourds en préparation."),
    dict(code="PDG", slug="protege-dents-gel-double", name="Protège-dents Gel Double", disc="boxe-anglaise",
         also=["muay-thai-kickboxing", "mma-grappling"], cat="protege-dents", shape="mouthguard",
         colors=[BLACK, RED], sizes=["S", "M"], price=24, step=0, material="silicone", level="debutant",
         closure="Thermoformable", origin="France", sales=730,
         short="Thermoformable, double gel, boîte ventilée incluse.",
         desc="Plongez 30 secondes dans l'eau chaude, mordez, refroidissez : ajustement sur mesure.\n\n- S : "
              "junior\n- M : adulte"),
    dict(code="COA", slug="coquille-acier-heritage", name="Coquille Heritage", disc="boxe-anglaise",
         also=["muay-thai-kickboxing", "mma-grappling"], cat="coquilles", shape="cup", colors=[LEATHER],
         sizes=["S", "M", "L", "XL"], price=39, step=0, material="synthetique", level="combat",
         closure="Ceinture élastique + scratch", origin="Pakistan", sales=210,
         short="Coque rigide et ceinture large : protection homologuée.",
         desc="Coque ABS doublée de mousse, ceinture élastique large pour un maintien sans irritation."),
    dict(code="SGS", slug="short-gala-satin", name="Short Gala Satin", disc="boxe-anglaise", cat="shorts",
         shape="shorts", colors=[BLACK, RED, WHITE], sizes=["XS", "S", "M", "L", "XL", "XXL"], price=49, step=0,
         material="polyester", level="combat", origin="Portugal", sales=188,
         short="Satin brillant, ceinture haute : la silhouette du ring.",
         desc="Taille haute élastiquée 12 cm, satin polyester léger qui ne colle pas."),
    # --- Muay Thaï & Kickboxing ---------------------------------------------------------------------
    dict(code="GNM", slug="gant-nak-muay-cuir", name="Gant Nak Muay Cuir", disc="muay-thai-kickboxing",
         cat="gants", shape="glove", colors=[LEATHER, BLACK], weights=OZ, price=129, step=5, material="cuir",
         level="sparring", range="pro", padding="Mousse latex répartie", closure="Scratch",
         origin="Bangkok, Thaïlande", featured=True, sales=325,
         short="Manchette courte et paume souple : pensé pour le clinch.",
         desc="La forme thaïlandaise traditionnelle : plus de rembourrage sur le dos de main, paume souple pour "
              "saisir en clinch."),
    dict(code="PTC", slug="protege-tibias-cuir-pro", name="Protège-tibias Cuir Pro", disc="muay-thai-kickboxing",
         also=["mma-grappling"], cat="protege-tibias", shape="shin", colors=[BLACK, LEATHER],
         sizes=["S", "M", "L", "XL"], price=139, step=0, material="cuir", level="combat", range="pro",
         padding="Mousse haute densité 30 mm", closure="Double scratch", origin="Thaïlande", featured=True,
         sales=260, low=True,
         short="Cuir pleine fleur, coque couvrant le cou-de-pied : sparring et combat.",
         desc="Protection intégrale tibia et cou-de-pied. Les deux sangles larges évitent la rotation pendant "
              "les échanges."),
    dict(code="PTM", slug="protege-tibias-mousse-sparring", name="Protège-tibias Sparring Microfibre",
         disc="muay-thai-kickboxing", cat="protege-tibias", shape="shin", colors=[RED, BLACK],
         sizes=["S", "M", "L", "XL"], price=79, step=0, material="microfibre", level="sparring",
         padding="Mousse double densité 25 mm", closure="Double scratch", origin="Thaïlande", sales=402,
         short="Léger et bien maintenu pour l'entraînement quotidien.",
         desc="Microfibre facile d'entretien, cou-de-pied amovible."),
    dict(code="SMT", slug="short-muay-thai-traditionnel", name="Short Muay Thaï Traditionnel",
         disc="muay-thai-kickboxing", cat="shorts", shape="shorts", colors=[RED, BLACK, BLUE],
         sizes=["XS", "S", "M", "L", "XL", "XXL"], price=45, step=0, material="polyester", level="combat",
         origin="Thaïlande", sales=301,
         short="Satin, fentes latérales larges, ceinture 4 cm brodée.",
         desc="Coupe ample et fentes latérales pour une liberté totale dans les coups de pied hauts."),
    dict(code="CDN", slug="coudieres-neoprene", name="Coudières Néoprène", disc="muay-thai-kickboxing",
         cat="protections", shape="pads", colors=[BLACK], sizes=["S", "M", "L"], price=29, step=0,
         material="synthetique", level="sparring", padding="Insert mousse 10 mm", origin="Thaïlande", sales=120,
         short="Protège les coudes en sparring Muay Thaï.",
         desc="Néoprène gainant et insert mousse : obligatoire dans la plupart des clubs en sparring."),
    dict(code="GKM", slug="gant-kickboxing-microfibre", name="Gant Kickboxing Microfibre",
         disc="muay-thai-kickboxing", cat="gants", shape="glove", colors=[BLUE, BLACK], weights=OZ, price=79,
         step=3, material="microfibre", level="sparring", padding="Mousse injectée", closure="Scratch",
         origin="Pakistan", sales=210,
         short="Protection renforcée du dos de la main pour les blocages.",
         desc="Dos de main surdimensionné pour encaisser les blocages de coups de pied."),
    # --- MMA & Grappling --------------------------------------------------------------------------------
    dict(code="MGC", slug="gants-mma-combat", name="Gants MMA Combat", disc="mma-grappling", cat="gants",
         shape="mma_glove", colors=[BLACK, RED], sizes=["S", "M", "L", "XL"], price=69, step=0, material="cuir",
         level="combat", range="competition", padding="Mousse 15 mm", closure="Scratch croisé",
         origin="Pakistan", chart="mma", sales=133,
         short="4 oz, doigts libres : le gant réglementaire de cage.",
         desc="Rembourrage 15 mm sur les phalanges, paume ouverte pour les saisies."),
    dict(code="MGS", slug="gants-mma-sparring-7oz", name="Gants MMA Sparring 7 oz", disc="mma-grappling",
         cat="gants", shape="mma_glove", colors=[OLIVE, BLACK], sizes=["S", "M", "L", "XL"], price=89, step=0,
         material="microfibre", level="sparring", padding="Mousse 25 mm", closure="Scratch large",
         origin="Pakistan", chart="mma", sales=154, low=True,
         short="Plus de protection pour frapper fort à l'entraînement.",
         desc="Un gant hybride qui protège vos partenaires sans vous empêcher de lutter."),
    dict(code="RCL", slug="rashguard-compression-manches-longues", name="Rashguard Compression Manches longues",
         disc="mma-grappling", also=["jiu-jitsu-bresilien"], cat="rashguards", shape="rashguard",
         colors=[BLACK, OLIVE], sizes=["XS", "S", "M", "L", "XL", "XXL"], price=55, step=0, material="polyester",
         level="sparring", origin="Portugal", sales=276,
         short="Compression graduée, coutures plates, séchage rapide.",
         desc="Protège la peau des brûlures de tapis et limite la transmission des infections cutanées."),
    dict(code="SMH", slug="short-mma-hybride", name="Short MMA Hybride", disc="mma-grappling", cat="shorts",
         shape="shorts", colors=[BLACK, OLIVE], sizes=["XS", "S", "M", "L", "XL", "XXL"], price=59, step=0,
         material="polyester", level="combat", origin="Portugal", sales=198,
         short="Stretch 4 directions, fermeture velcro + cordon.",
         desc="Fente d'entrejambe stretch pour les gardes fermées et les coups de pied hauts."),
    dict(code="PDP", slug="protege-dents-pro-thermoformable", name="Protège-dents Pro sur-mesure",
         disc="mma-grappling", also=["boxe-anglaise", "muay-thai-kickboxing"], cat="protege-dents",
         shape="mouthguard", colors=[WHITE, BLACK], sizes=["M"], price=39, step=0, material="silicone",
         level="combat", range="pro", closure="Thermoformable 2 passes", origin="France", sales=180,
         short="Double couche EVA : absorption maximale pour le combat.",
         desc="Formage en deux passes pour une tenue parfaite sans gêner la respiration."),
    dict(code="TPM", slug="protege-tibias-mma-socks", name="Protège-tibias MMA Chaussette",
         disc="mma-grappling", cat="protege-tibias", shape="shin", colors=[BLACK], sizes=["S", "M", "L", "XL"],
         price=69, step=0, material="synthetique", level="sparring", padding="Mousse 15 mm",
         closure="Chaussette élastique", origin="Pakistan", sales=90,
         short="Chaussette élastique sans scratch : rien n'accroche au sol.",
         desc="Idéal pour le sparring MMA : pas de sangle qui se défait pendant la lutte."),
    # --- Jiu-Jitsu Brésilien ------------------------------------------------------------------------------
    dict(code="KJH", slug="kimono-jjb-heritage-450", name="Kimono JJB Heritage 450", disc="jiu-jitsu-bresilien",
         cat="kimonos", shape="kimono", colors=[WHITE, BLUE, BLACK], sizes=["S", "M", "L", "XL", "XXL"],
         price=149, step=0, material="coton", level="combat", range="competition", origin="Portugal",
         extra={"Grammage veste": "450 g/m² pearl weave", "Pantalon": "Ripstop 10 oz", "Norme": "IBJJF"},
         featured=True, sales=166,
         short="Pearl weave 450 g, coupe compétition IBJJF.",
         desc="Une veste dense qui résiste aux saisies sans être lourde.\n\n## Entretien\nLavage 30 °C, "
              "séchage à l'air libre uniquement."),
    dict(code="KJL", slug="kimono-jjb-leger-350", name="Kimono JJB Léger 350", disc="jiu-jitsu-bresilien",
         cat="kimonos", shape="kimono", colors=[WHITE, BLUE], sizes=["S", "M", "L", "XL", "XXL"], price=119,
         step=0, material="coton", level="debutant", origin="Portugal",
         extra={"Grammage veste": "350 g/m²", "Pantalon": "Coton sergé"}, sales=142,
         short="Léger et respirant : le kimono des longues séances d'été.",
         desc="Idéal pour débuter et pour voyager : il sèche en quelques heures."),
    dict(code="RJR", slug="rashguard-jjb-ranked", name="Rashguard JJB Ranked Manches courtes",
         disc="jiu-jitsu-bresilien", also=["mma-grappling"], cat="rashguards", shape="rashguard",
         colors=[WHITE, BLUE, BLACK], sizes=["XS", "S", "M", "L", "XL", "XXL"], price=49, step=0,
         material="polyester", level="sparring", origin="Portugal", sales=150,
         short="Couleur de ceinture, conforme aux règles No-Gi.",
         desc="Bandes de couleur selon votre grade, coutures plates anti-frottement."),
    dict(code="SGR", slug="short-grappling", name="Short Grappling No-Gi", disc="jiu-jitsu-bresilien",
         cat="shorts", shape="shorts", colors=[BLACK], sizes=["S", "M", "L", "XL"], price=45, step=0,
         material="polyester", level="sparring", origin="Portugal", sales=88,
         short="Sans poche ni rivet : rien qui accroche pendant les transitions.",
         desc="Tissu stretch déperlant, ceinture plate."),
    # --- Entraînement & Sacs de frappe -----------------------------------------------------------------
    dict(code="SFC", slug="sac-de-frappe-cuir-120", name="Sac de frappe Cuir 120 cm",
         disc="entrainement-sacs-de-frappe", also=["boxe-anglaise", "muay-thai-kickboxing"],
         cat="materiel-de-club", shape="bag", colors=[BLACK, LEATHER], price=349, step=0, material="cuir",
         level="combat", range="pro", padding="Textile compressé + sable en sacs", origin="Pakistan",
         extra={"Hauteur": "120 cm", "Diamètre": "35 cm", "Poids rempli": "40 kg", "Attache": "4 chaînes acier"},
         featured=True, sales=74, low=True,
         short="Cuir épais, 40 kg prêt à suspendre : il encaisse des années de travail.",
         desc="Remplissage textile compressé et sable : frappe dense sans point dur.\n\n## Installation\n"
              "Prévoir une attache plafond supportant 150 kg minimum."),
    dict(code="SFT", slug="sac-thai-180-microfibre", name="Sac Thaï long 180 cm",
         disc="entrainement-sacs-de-frappe", also=["muay-thai-kickboxing"], cat="materiel-de-club", shape="bag",
         colors=[RED, BLACK], price=279, step=0, material="microfibre", level="sparring",
         padding="Textile compressé", origin="Thaïlande",
         extra={"Hauteur": "180 cm", "Poids rempli": "50 kg"}, sales=58,
         short="Le sac long pour travailler les low-kicks et les genoux.",
         desc="Sa longueur permet de travailler du bas des jambes jusqu'à la tête."),
    dict(code="PDO", slug="pattes-d-ours-cuir", name="Pattes d'ours Cuir incurvées",
         disc="entrainement-sacs-de-frappe", also=["boxe-anglaise"], cat="materiel-de-club", shape="pads",
         colors=[BLACK, LEATHER], price=89, step=0, material="cuir", level="sparring", range="pro",
         padding="Mousse gel incurvée", closure="Scratch intérieur", origin="Pakistan", sales=121,
         short="Forme incurvée pour des enchaînements fluides côté coach.",
         desc="Le coach garde la main fermée naturellement : moins de fatigue sur les longues séances."),
    dict(code="PAO", slug="paos-thai-paire", name="Paos Thaï (paire)", disc="entrainement-sacs-de-frappe",
         also=["muay-thai-kickboxing"], cat="materiel-de-club", shape="pads", colors=[RED, BLACK], price=119,
         step=0, material="cuir", level="combat", range="pro", padding="Mousse multicouche 10 cm",
         closure="Double poignée + sangle", origin="Thaïlande", sales=97,
         short="Paos épais pour encaisser les kicks du clinch au middle.",
         desc="Vendu par paire. Poignées doublées pour un maintien ferme."),
    dict(code="CAS", slug="corde-a-sauter-acier", name="Corde à sauter Acier Speed",
         disc="entrainement-sacs-de-frappe", also=["boxe-anglaise"], cat="materiel-de-club", shape="rope",
         colors=[BLACK, RED], price=29, step=0, material="autre", level="debutant", origin="Taïwan",
         extra={"Câble": "Acier gainé 2,5 mm", "Longueur": "Réglable jusqu'à 3 m"}, sales=520,
         short="Câble acier gainé, roulements à billes : pour le cardio du boxeur.",
         desc="Longueur réglable sans outil. Les roulements assurent une rotation fluide à haute vitesse."),
    # --- Bandages & Soins ------------------------------------------------------------------------------------
    dict(code="BDB", slug="bandes-de-boxe-450", name="Bandes de boxe 4,5 m", disc="boxe-anglaise",
         also=["muay-thai-kickboxing", "mma-grappling", "entrainement-sacs-de-frappe"], cat="bandages-soins",
         shape="wraps", colors=[BLACK, RED, WHITE], price=9.9, step=0, material="coton", level="debutant",
         closure="Boucle pouce + scratch", origin="Pakistan", sales=980, low=True,
         short="Coton semi-élastique 4,5 m : la base de toute protection des mains.",
         desc="Longueur adulte pour un bandage complet des métacarpes et du poignet."),
    dict(code="BGR", slug="sous-gants-gel-rapides", name="Sous-gants Gel rapides", disc="boxe-anglaise",
         also=["muay-thai-kickboxing"], cat="bandages-soins", shape="wraps", colors=[BLACK],
         sizes=["S", "M", "L"], price=19, step=0, material="silicone", level="debutant", origin="Chine",
         sales=260, short="Enfilez, serrez, frappez : la protection en 10 secondes.",
         desc="Insert gel sur les phalanges et bande de poignet intégrée."),
    dict(code="BCR", slug="baume-entretien-cuir", name="Baume d'entretien Cuir", disc="boxe-anglaise",
         also=["muay-thai-kickboxing", "entrainement-sacs-de-frappe"], cat="bandages-soins", shape="tin",
         colors=[LEATHER], price=14.9, step=0, material="autre", level="debutant", origin="France",
         extra={"Contenance": "100 ml", "Composition": "Cire d'abeille, huile de pied de bœuf"}, sales=233,
         short="Nourrit et imperméabilise le cuir des gants et protections.",
         desc="Appliquez une noisette au chiffon doux une fois par mois. Voir notre guide d'entretien."),
    dict(code="DGS", slug="spray-assainissant-gants", name="Spray assainissant Gants", disc="boxe-anglaise",
         also=["muay-thai-kickboxing", "mma-grappling"], cat="bandages-soins", shape="bottle", colors=[RED],
         price=12, step=0, material="autre", level="debutant", origin="France",
         extra={"Contenance": "150 ml"}, sales=310,
         short="Neutralise les odeurs et assainit l'intérieur des gants.",
         desc="À vaporiser après chaque séance, gants ouverts, puis laisser sécher à l'air libre."),
]

GUIDES = [
    {
        "slug": "choisir-poids-gants-oz", "title": "Comment choisir le poids de ses gants en oz ?",
        "kicker": "Guide technique", "minutes": 6,
        "excerpt": "8, 10, 12, 14 ou 16 oz ? Le poids d'un gant ne dépend pas que de votre gabarit : l'usage "
                   "compte tout autant. Notre méthode pour ne pas se tromper.",
        "categories": ["gants"],
        "products": ["gant-cuir-heritage-pro", "gant-sparring-microfibre", "gant-combat-lacets-championnat",
                     "gant-initiation-club", "gant-nak-muay-cuir", "gant-kickboxing-microfibre"],
        "body": "L'once (oz) mesure la masse du gant : 1 oz = 28,35 g. Un gant de 14 oz pèse donc environ 400 g. "
                "Plus il est lourd, plus il contient de rembourrage.\n\n"
                "## Règle n° 1 : l'usage avant le gabarit\n"
                "- **Sac et pattes d'ours** : un gant plus léger (10–12 oz) pour garder de la vitesse.\n"
                "- **Sparring** : 14 à 16 oz pour protéger votre partenaire, quel que soit votre niveau.\n"
                "- **Compétition** : 8 ou 10 oz selon la catégorie de poids et le règlement.\n\n"
                "## Règle n° 2 : votre poids de corps\n"
                "Moins de 60 kg : 10–12 oz. De 60 à 75 kg : 12–14 oz. Au-delà de 75 kg : 16 oz. Au-delà de "
                "90 kg : envisagez 18 oz en sparring.\n\n"
                "## Règle n° 3 : la main bandée\n"
                "Essayez toujours vos gants avec vos bandes. La main doit pouvoir se fermer complètement, sans "
                "jeu au niveau du poignet.\n\n"
                "## Cuir ou microfibre ?\n"
                "Le cuir épouse la main avec le temps et dure plus longtemps ; la microfibre est plus facile à "
                "entretenir et plus économique. Pour un usage intensif, le cuir reste l'investissement le plus "
                "rentable.",
    },
    {
        "slug": "entretien-du-cuir", "topic": "entretien", "title": "Entretien du cuir : faire durer ses gants et protections",
        "kicker": "Savoir-faire", "minutes": 4,
        "excerpt": "Un gant en cuir bien entretenu dure trois fois plus longtemps. Séchage, nettoyage, nutrition : "
                   "la routine qui préserve votre matériel.",
        "categories": [],
        "products": ["gant-cuir-heritage-pro", "gant-combat-lacets-championnat", "gant-nak-muay-cuir",
                     "protege-tibias-cuir-pro", "casque-ouvert-cuir", "sac-de-frappe-cuir-120",
                     "pattes-d-ours-cuir", "baume-entretien-cuir", "spray-assainissant-gants"],
        "body": "La sueur est l'ennemie du cuir : elle est acide, salée et nourrit les bactéries. La routine "
                "suivante prend deux minutes par séance.\n\n"
                "## Après chaque séance\n"
                "- Retirez vos bandes et ouvrez grand les gants.\n"
                "- Vaporisez un spray assainissant à l'intérieur.\n"
                "- Laissez sécher à l'air libre, **jamais** sur un radiateur ni au soleil direct.\n\n"
                "## Chaque semaine\n"
                "Essuyez l'extérieur avec un chiffon légèrement humide, puis séchez.\n\n"
                "## Chaque mois\n"
                "Appliquez une noisette de baume au chiffon doux, en mouvements circulaires, puis lustrez. "
                "Le cuir retrouve sa souplesse et résiste mieux aux craquelures.\n\n"
                "## À éviter\n"
                "- Le sac de sport fermé avec les gants humides à l'intérieur.\n"
                "- Les produits ménagers et l'alcool, qui dessèchent le cuir.",
    },
    {
        "slug": "choisir-protege-tibias", "title": "Protège-tibias : trouver la bonne taille et le bon modèle",
        "kicker": "Guide technique", "minutes": 5, "topic": "protections",
        "excerpt": "Mousse, cuir ou chaussette : chaque modèle répond à un usage. La taille se choisit à la "
                   "longueur du tibia, pas à la pointure.",
        "categories": ["protege-tibias"],
        "products": ["protege-tibias-cuir-pro", "protege-tibias-mousse-sparring", "protege-tibias-mma-socks",
                     "paos-thai-paire"],
        "body": "Un protège-tibias doit couvrir l'os du genou jusqu'au cou-de-pied, sans gêner la flexion de la "
                "cheville. Trop court, il laisse le tibia exposé ; trop long, il bascule à chaque check.\n\n"
                "## Mesurer avant d'acheter\n"
                "Mesurez du bas de la rotule jusqu'au pli de la cheville, jambe tendue. Reportez la mesure et votre "
                "poids sur le tableau ci-dessous : en cas d'hésitation, prenez la taille au-dessus.\n\n"
                "## Trois familles de protège-tibias\n"
                "- **Mousse moulée avec pied** : le standard du sparring en muay thaï, il protège aussi le dessus "
                "du pied.\n"
                "- **Cuir pro** : plus dense, il encaisse les entraînements intensifs et garde sa forme des années.\n"
                "- **Chaussette (sock)** : léger et maintenu sans scratch, il convient au MMA et aux enchaînements "
                "avec lutte.\n\n"
                "## Le bon maintien\n"
                "Deux scratchs larges valent mieux que trois fins. Après dix minutes de shadow, la protection ne "
                "doit ni tourner ni glisser.",
    },
    {
        "slug": "poser-ses-bandes-de-boxe", "title": "Poser ses bandes de boxe en 8 étapes",
        "kicker": "Débuter", "minutes": 4, "topic": "debutant",
        "excerpt": "Les bandes maintiennent le poignet et protègent les métacarpes. Une pose correcte prend une "
                   "minute ; voici la méthode enseignée en club.",
        "categories": ["bandages-soins"],
        "products": ["bandes-de-boxe-450", "sous-gants-gel-rapides", "gant-initiation-club",
                     "spray-assainissant-gants"],
        "body": "Une bande de 4,5 m suffit pour la plupart des mains. En dessous, le poignet est mal tenu ; "
                "au-delà, le gant devient difficile à enfiler.\n\n"
                "## La méthode en 8 étapes\n"
                "- Passez la boucle autour du pouce, bande vers le dos de la main.\n"
                "- Faites trois tours autour du poignet, sans serrer au point de bloquer la circulation.\n"
                "- Remontez en diagonale sur le dos de la main.\n"
                "- Faites trois tours autour des articulations, doigts écartés.\n"
                "- Passez entre chaque doigt en revenant par le poignet.\n"
                "- Faites un tour autour du pouce pour le verrouiller.\n"
                "- Repassez sur les articulations pour les rembourrer.\n"
                "- Terminez au poignet et fermez le scratch.\n\n"
                "## Le test\n"
                "Fermez le poing : il doit se fermer complètement, sans fourmillement. Si les doigts bleuissent, "
                "recommencez en serrant moins.",
    },
    {
        "slug": "choisir-kimono-jjb", "title": "Kimono de JJB : taille, grammage et rétrécissement",
        "kicker": "Débuter", "minutes": 5, "topic": "debutant",
        "excerpt": "A1, A2, 350 ou 450 g/m² : comment lire l'étiquette d'un kimono et éviter la mauvaise "
                   "surprise du premier lavage.",
        "categories": ["kimonos"],
        "products": ["kimono-jjb-heritage-450", "kimono-jjb-leger-350", "rashguard-jjb-ranked", "short-grappling"],
        "body": "Les kimonos de jiu-jitsu brésilien se taillent par la lettre A (adulte) suivie d'un chiffre de "
                "0 à 5. Le chiffre dépend d'abord de votre taille, ensuite de votre poids.\n\n"
                "## Le grammage\n"
                "- **350 g/m²** : léger, il sèche vite et convient aux climats chauds et aux entraînements "
                "quotidiens.\n"
                "- **450 g/m²** : plus épais, il résiste mieux aux saisies et dure plus longtemps en "
                "compétition.\n\n"
                "## Le rétrécissement\n"
                "Un kimono en coton peut perdre 3 à 5 % au premier lavage. Lavez à 30 °C, séchez à l'air libre "
                "et évitez le sèche-linge.\n\n"
                "## Les règles de compétition\n"
                "La manche doit arriver à 5 cm du poignet bras tendu, et le pantalon à 5 cm de la malléole. "
                "Vérifiez-le avant de vous inscrire.",
    },
    {
        "slug": "choisir-sac-de-frappe", "title": "Choisir son sac de frappe : poids, hauteur et remplissage",
        "kicker": "Guide technique", "minutes": 6, "topic": "debutant",
        "excerpt": "Un sac trop léger se balance, un sac trop lourd abîme les poignets. La règle simple : la moitié "
                   "de votre poids de corps.",
        "categories": ["materiel-de-club"],
        "products": ["sac-de-frappe-cuir-120", "sac-thai-180-microfibre", "pattes-d-ours-cuir",
                     "gant-sparring-microfibre", "bandes-de-boxe-450"],
        "body": "Le sac de frappe est l'investissement central d'une salle à domicile. Trois critères comptent : "
                "son poids, sa hauteur et la manière dont il est rempli.\n\n"
                "## Le poids\n"
                "Visez environ la moitié de votre poids de corps : un sac de 35 à 40 kg convient à un pratiquant "
                "de 75 kg. Plus léger, il bouge trop ; plus lourd, il devient dur comme un mur.\n\n"
                "## La hauteur\n"
                "- **120 cm** : boxe anglaise, travail des poings et des crochets au corps.\n"
                "- **180 cm** : muay thaï et kickboxing, pour frapper aussi en low-kick.\n\n"
                "## Le remplissage\n"
                "Un mélange de chutes textiles et de sable ensaché répartit le poids sans créer de zone dure. "
                "Faites-le tourner d'un quart de tour chaque mois pour éviter qu'il ne se tasse.\n\n"
                "## L'installation\n"
                "Fixez-le à une poutre ou à une potence capable de supporter trois fois son poids, et laissez "
                "un mètre libre tout autour.",
    },
]

REVIEWS = [
    ("gant-cuir-heritage-pro", "Karim B.", 5, "Le meilleur gant que j'ai eu",
     "Cuir superbe, rembourrage qui ne s'écrase pas après 6 mois de sparring 3 fois par semaine."),
    ("gant-cuir-heritage-pro", "Julie M.", 4, "Excellent, un peu raide au début",
     "Il faut une dizaine de séances pour qu'il se fasse à la main, ensuite c'est parfait."),
    ("gant-sparring-microfibre", "Thomas L.", 5, "Rapport qualité-prix imbattable",
     "J'ai équipé toute la section loisirs du club avec, aucun retour négatif."),
    ("protege-tibias-cuir-pro", "Anong S.", 5, "Ne bouge pas d'un millimètre",
     "Les deux sangles larges font toute la différence en sparring."),
    ("kimono-jjb-heritage-450", "Rafael C.", 4, "Solide",
     "Le tissage est dense, attention il rétrécit un peu au premier lavage, prendre la taille au-dessus."),
    ("bandes-de-boxe-450", "Inès D.", 5, "Indispensable", "Bonne longueur, le coton tient bien au lavage."),
]

PAGE_META = [
    ("/", "Accueil", "Boxing Shop — Équipement de boxe et d'arts martiaux",
     "Gants, protections, tenues et matériel de club pour la boxe anglaise, le Muay Thaï, le MMA et le JJB. "
     "Livraison offerte dès 90 €."),
    ("/guides/", "Guides techniques", "Guides techniques — bien choisir son équipement",
     "Poids des gants, tailles, entretien du cuir : nos conseils d'experts pour choisir et entretenir votre "
     "matériel de sports de combat."),
    ("/boutique/", "Boutique", "Tout le catalogue — Boxing Shop",
     "Filtrez par discipline, poids, taille, matière et niveau : tout l'équipement de combat en un coup d'œil."),
]
