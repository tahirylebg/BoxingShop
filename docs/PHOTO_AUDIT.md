# Audit des photos produit

Règle (19/11/2026) : aucune illustration, aucun dessin, aucun placeholder. Chaque couleur vendue a sa propre
**photo réelle** (Pexels, licence libre) montrant le bon objet dans la bonne couleur ; sinon la couleur est retirée,
et un produit sans aucune photo est retiré du seed. Chaque photo a été ouverte et regardée dans son cadrage
d'affichage (4:5). Photos produit sans désaturation ; les photos d'ambiance (sans couleur) ne servent qu'au survol
des cartes et en fin de galerie. Crédits : `CREDITS.md`. Source de vérité : `catalog/demo_photos.py`
(`PRODUCT_COLOR_PHOTOS`).

Bilan : **26** couleurs avec photo, **11** couleurs retirées, **17** produits retirés
(17 produits en ligne).

| Produit | Couleur | Fichier (`media/demo/`) | Statut |
|---|---|---|---|
| Gant Heritage Cuir Pro | Noir | `products/prod-gants-noirs.jpg` | OK — photo réelle vérifiée |
| Gant Heritage Cuir Pro | Rouge | `products/prod-gants-rouges-1.jpg`, `products/prod-gants-rouges-2.jpg` | OK — photo réelle vérifiée |
| Gant de combat Lacets Championnat | Rouge | `products/prod-gants-rouges-1.jpg` | OK — photo réelle vérifiée |
| Gant de combat Lacets Championnat | Noir | `products/prod-gants-noirs.jpg` | OK — photo réelle vérifiée |
| Gant Sparring Microfibre | Noir | `products/prod-gants-noirs.jpg` | OK — photo réelle vérifiée |
| Gant Sparring Microfibre | Blanc | `products/prod-gants-blancs-2.jpg`, `products/prod-gants-blancs.jpg` | OK — photo réelle vérifiée |
| Gant Initiation Club | Rouge | `products/prod-gants-rouges-2.jpg`, `products/prod-gants-rouges-1.jpg` | OK — photo réelle vérifiée |
| Gant Initiation Club | Bleu | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Casque ouvert Cuir | Noir | `products/prod-casque-noir.jpg` | OK — photo réelle vérifiée |
| Casque ouvert Cuir | Rouge | `products/prod-casque-rouge.jpg` | OK — photo réelle vérifiée |
| Casque à barre Sparring | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Protège-dents Gel Double | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Protège-dents Gel Double | Rouge | — | Produit retiré (aucune photo réelle crédible) |
| Coquille Heritage | Fauve | — | Produit retiré (aucune photo réelle crédible) |
| Short Gala Satin | Noir | `products/prod-short-noir.jpg` | OK — photo réelle vérifiée |
| Short Gala Satin | Rouge | `products/prod-short-rouge.jpg` | OK — photo réelle vérifiée |
| Short Gala Satin | Blanc | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Gant Nak Muay Cuir | Fauve | `products/prod-gants-fauves.jpg` | OK — photo réelle vérifiée |
| Gant Nak Muay Cuir | Noir | `products/prod-gants-noirs.jpg` | OK — photo réelle vérifiée |
| Protège-tibias Cuir Pro | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Protège-tibias Cuir Pro | Fauve | — | Produit retiré (aucune photo réelle crédible) |
| Protège-tibias Sparring Microfibre | Rouge | — | Produit retiré (aucune photo réelle crédible) |
| Protège-tibias Sparring Microfibre | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Short Muay Thaï Traditionnel | Rouge | — | Produit retiré (aucune photo réelle crédible) |
| Short Muay Thaï Traditionnel | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Short Muay Thaï Traditionnel | Bleu | — | Produit retiré (aucune photo réelle crédible) |
| Coudières Néoprène | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Gant Kickboxing Microfibre | Bleu | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Gant Kickboxing Microfibre | Noir | `products/prod-gants-noirs.jpg` | OK — photo réelle vérifiée |
| Gants MMA Combat | Noir | `products/prod-mma-noirs.jpg` | OK — photo réelle vérifiée |
| Gants MMA Combat | Rouge | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Gants MMA Sparring 7 oz | Kaki | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Gants MMA Sparring 7 oz | Noir | `products/prod-mma-noirs.jpg` | OK — photo réelle vérifiée |
| Rashguard Compression Manches longues | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Rashguard Compression Manches longues | Kaki | — | Produit retiré (aucune photo réelle crédible) |
| Short MMA Hybride | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Short MMA Hybride | Kaki | — | Produit retiré (aucune photo réelle crédible) |
| Protège-dents Pro sur-mesure | Blanc | `products/prod-protege-dents-blanc.jpg` | OK — photo réelle vérifiée |
| Protège-dents Pro sur-mesure | Noir | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Protège-tibias MMA Chaussette | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Kimono JJB Heritage 450 | Blanc | `products/prod-kimono-blanc.jpg`, `products/prod-kimono-blanc-2.jpg` | OK — photo réelle vérifiée |
| Kimono JJB Heritage 450 | Bleu | `products/prod-kimono-bleu.jpg` | OK — photo réelle vérifiée |
| Kimono JJB Heritage 450 | Noir | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Kimono JJB Léger 350 | Blanc | `products/prod-kimono-blanc-2.jpg`, `products/prod-kimono-blanc.jpg` | OK — photo réelle vérifiée |
| Kimono JJB Léger 350 | Bleu | `products/prod-kimono-bleu.jpg` | OK — photo réelle vérifiée |
| Rashguard JJB Ranked Manches courtes | Blanc | — | Produit retiré (aucune photo réelle crédible) |
| Rashguard JJB Ranked Manches courtes | Bleu | — | Produit retiré (aucune photo réelle crédible) |
| Rashguard JJB Ranked Manches courtes | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Short Grappling No-Gi | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Sac de frappe Cuir 120 cm | Noir | `products/prod-sac-noir.jpg` | OK — photo réelle vérifiée |
| Sac de frappe Cuir 120 cm | Fauve | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Sac Thaï long 180 cm | Rouge | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Sac Thaï long 180 cm | Noir | `products/prod-sac-noir.jpg` | OK — photo réelle vérifiée |
| Pattes d'ours Cuir incurvées | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Pattes d'ours Cuir incurvées | Fauve | — | Produit retiré (aucune photo réelle crédible) |
| Paos Thaï (paire) | Rouge | — | Produit retiré (aucune photo réelle crédible) |
| Paos Thaï (paire) | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Corde à sauter Acier Speed | Noir | `products/prod-corde-noire.jpg` | OK — photo réelle vérifiée |
| Corde à sauter Acier Speed | Rouge | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Bandes de boxe 4,5 m | Noir | `products/prod-bandes-noires.jpg` | OK — photo réelle vérifiée |
| Bandes de boxe 4,5 m | Rouge | — | Couleur retirée (aucune photo réelle de cette couleur) |
| Bandes de boxe 4,5 m | Blanc | `products/prod-bandes-blanches.jpg` | OK — photo réelle vérifiée |
| Sous-gants Gel rapides | Noir | — | Produit retiré (aucune photo réelle crédible) |
| Baume d'entretien Cuir | Fauve | — | Produit retiré (aucune photo réelle crédible) |
| Spray assainissant Gants | Rouge | — | Produit retiré (aucune photo réelle crédible) |

## Photos écartées après vérification visuelle

| Pexels | Prévue pour | Motif |
|---|---|---|
| 12661476 | Gants bleus | Gants coupés en haut du cadre, le boxeur domine |
| 29015505 | Short MMA noir | Short à peine visible, les gants dominent |
| 6339721 | Corde à sauter | Haltères rouges et poignées bleues dominent |
| 7005124 | Short rouge | Le gant au premier plan masque le short |
| 7289912 | Protège-dents noir | Les gants dominent l'image |
| 6296049 | Sac rouge | Personne au premier plan, sac en bord de cadre |
| 6296115 | Paos / pattes d'ours | Plusieurs objets de couleurs mélangées |
| 4761665 | Casque à barre | Casque ouvert, pas à barre |
| 3290709 | Bandes rouges | Bande en réalité blanche |
| 14898688 | Casque noir | Noir et blanc : couleur invérifiable |
