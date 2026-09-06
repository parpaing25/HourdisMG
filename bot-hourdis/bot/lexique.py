"""Le vocabulaire du métier : hourdis, terre cuite, plancher, toiture.

Trois langues, parce que les sources sont françaises (fabricants, presse du
bâtiment, chaînes de maçons), malgaches (pages et groupes de Tana) et parfois
anglaises (tutos internationaux sur les planchers à poutrelles).

Chaque mot porte un POIDS : « hourdis » ou « entrevous » disent le sujet à eux
seuls ; « béton » ou « chantier » ne le disent qu'accompagnés. Les motifs sont
des expressions régulières sur du texte MIS EN MINUSCULES ET SANS ACCENTS
(voir `score.sans_accents`) — d'où « beton », « etaiement », « chainage ».
"""
from __future__ import annotations

# (motif, poids). Les motifs longs d'abord : « plancher hourdis » doit compter
# comme tel avant que « plancher » et « hourdis » ne comptent séparément.
MOTS_METIER: list[tuple[str, int]] = [
    # ── Le cœur : plancher à poutrelles et hourdis ──
    (r"plancher[s]? (a |en )?(poutrelles?|hourdis)", 14),
    (r"poutrelles?[- ]hourdis", 14),
    (r"hourdis", 10),
    (r"entrevous", 10),
    (r"poutrelles?", 7),
    (r"dalle de compression", 9),
    (r"predalles?", 6),
    (r"planchers? (beton|intermediaire|haut|bas|d'etage)", 6),
    (r"plancher[s]?", 3),
    (r"rihana", 6),                       # mg : plancher / étage
    (r"lalotra", 3),                      # mg : dalle / enduit
    (r"gorodona", 4),                     # mg : plancher
    # ── Terre cuite ──
    (r"terre[- ]cuite", 9),
    (r"briques? (creuses?|alveolaires?|monomur|de terre cuite|rouge)", 9),
    (r"bloc[s]? (de )?terre cuite", 8),
    (r"briquettes?", 6),
    (r"plaquettes? (de parement|murales?|terre cuite)", 7),
    (r"briques?", 4),
    (r"biriky", 7),                       # mg : brique
    (r"tanimanga", 6),                    # mg : argile, terre cuite
    (r"tuiles? (mecaniques?|canal|a emboitement|plates?|ecailles?|terre cuite|romanes?)", 9),
    (r"tuiles?", 5),
    (r"tafo(n-trano|ntrano)?", 4),        # mg : toit
    (r"monomur", 7),
    (r"four[s]? a briques?", 6),
    (r"cuisson (des )?(briques?|tuiles?)", 6),
    (r"argile", 3),
    # ── La pose, le gros œuvre ──
    (r"etaiement|etais? de chantier|etayer", 6),
    (r"chainages?", 5),
    (r"treillis soude", 5),
    (r"ferraillage|armatures?", 4),
    (r"coffrage", 4),
    (r"linteaux?", 4),
    (r"coulage|couler la dalle", 4),
    (r"beton", 3),
    (r"mortier|ciment", 3),
    (r"macon(nerie|s)?", 4),
    (r"gros[- ]oeuvre", 4),
    (r"chantiers?", 2),
    (r"fanorenana", 5),                   # mg : construction
    (r"trano (vato|biriky)", 5),          # mg : maison en dur / en brique
    (r"mpanao trano|mpandrafitra|mason", 4),   # mg : maçon, ouvrier du bâtiment
    (r"simenitra", 3),                    # mg : ciment
    (r"vy (fer|beton)|fer a beton|fers? tor", 3),
    # ── Anglais ──
    (r"hollow (clay|core) (blocks?|slabs?)", 9),
    (r"beam[- ]and[- ]block", 10),
    (r"clay (blocks?|bricks?|tiles?|roof)", 7),
    (r"terracotta", 6),
    (r"precast (beams?|slab|concrete floor)", 5),
    (r"suspended floor", 5),
    (r"bricks?", 3),
    (r"roof tiles?", 5),
    # ── Performances et arguments (éducatif) ──
    (r"isolation (thermique|phonique)|inertie thermique", 4),
    (r"portee|surcharge|resistance", 2),
    (r"economie de beton|leger|legerete", 3),
]

# Ce qui fait un CONSEIL, un TUTO, une leçon — plutôt qu'une simple mention.
TUTORIEL = (
    r"\b(comment|tuto(riel)?s?|etapes?|guide|conseils?|astuces?|erreurs?|"
    r"a eviter|technique|methode|calcul(er)?|combien|pourquoi|bien poser|"
    r"mise en oeuvre|pose (d'un|du|des|de)|regles? de l'art|dtu|"
    r"ahoana|torohevitra|fomba|tsy azo atao|hadisoana|"
    r"how to|step[- ]by[- ]step|tips?|mistakes?|guide)\b"
)

# Thème -> motif. Un texte peut porter plusieurs thèmes.
THEMES: dict[str, str] = {
    "pose": r"pose|poser|mise en oeuvre|installation|montage|etapes?|apetraka|fametrahana|install",
    "calcul": r"calcul|combien|quantite|nombre de|par m2|m²|au metre|portee|dimensionn|isa|firy",
    "erreurs": r"erreurs?|a eviter|piege|defaut|fissur|malfacon|hadisoana|mistake|fail",
    "comparatif": r"compar|versus|\bvs\b|ou bien|plutot que|difference|avantages?|inconvenients?|sa ",
    "isolation": r"isolation|thermique|phonique|acoustique|inertie|chaleur|hafanana",
    "toiture": r"toit|toiture|couverture|tuile|charpente|tafo|roof",
    "murs": r"\bmurs?\b|cloison|parement|facade|rindrina|wall",
    "plancher": r"plancher|hourdis|entrevous|poutrelle|dalle|rihana|slab|floor",
    "etaiement": r"etai|etaiement|etayage|coffrage|shoring|formwork",
    "securite": r"securite|accident|chute|protection|epi\b|casque|fiarovana",
    "fabrication": r"fabrication|fabriqu|cuisson|four|argile|sechage|usine|production",
    "prix": r"prix|tarif|cout|budget|ariary|\bar\b|euros?|vidiny|price|cost",
    "entretien": r"entretien|renovation|reparation|fuite|humidite|mousse|nettoyage",
    "madagascar": r"madagascar|madagasikara|antananarivo|tana\b|ambohimanga|malagasy|malgache",
}

# Ce qui trahit un hors-sujet : le mot est là, le sujet non.
REPOUSSOIRS: list[tuple[str, str]] = [
    ("annonce immobilière", r"\b(a vendre|avendre|amidy|ahofa|a louer|alouer|mivarotra trano|"
                            r"terrain titre|titre borne|villa f\d|appartement t\d)\b"),
    ("offre d'emploi", r"\b(recrut|offre d'emploi|tolotr'?asa|cv a envoyer|poste a pourvoir)\b"),
    ("brique alimentaire", r"\bbriques? (de|d')\s?(lait|jus|soupe|creme|coco)\b"),
    ("jeu / Lego", r"\b(lego|minecraft|briques? de construction (pour )?enfants?|jouets?)\b"),
    ("informatique", r"\b(tuiles? (d'interface|graphiques?|windows)|tile ?set|plancher de verre|"
                     r"javascript|plugin|wordpress theme)\b"),
    ("pari / casino", r"\b(casino|paris? sportifs?|bookmaker|loto)\b"),
    ("fer plat / autre métier", r"\b(hourdis de tole|bardage seul)\b"),
]

# Mots vides pour deviner la langue. Volontairement courts et fréquents.
LANGUES: dict[str, tuple[str, ...]] = {
    "mg": ("ny", "sy", "amin", "amin'ny", "ary", "izay", "dia", "ho", "no", "tsy", "misy",
           "ireo", "koa", "fa", "raha", "mba", "efa", "tokony", "azo", "anao", "isika", "io"),
    "fr": ("le", "la", "les", "des", "et", "pour", "une", "dans", "est", "avec", "sur", "pas",
           "que", "qui", "vous", "nous", "sont", "cette", "plus", "aussi", "du", "au"),
    "en": ("the", "and", "of", "to", "with", "for", "is", "are", "you", "this", "that", "on",
           "your", "it", "in", "be", "can", "will", "from", "or"),
}

# Bonus par genre de trouvaille : une vidéo de pose se partage mieux qu'un
# communiqué ; un PDF de fabricant est une référence technique.
BONUS_GENRE = {"video": 8, "pdf": 5, "article": 0, "actualite": -2, "post_fb": 0}
