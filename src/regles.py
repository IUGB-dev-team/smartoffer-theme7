"""
VERSION 1 — Le moteur de règles (démarrage à froid).

On transforme les réponses du questionnaire en un "besoin" en Mb/s,
puis on choisit le plus petit forfait qui couvre ce besoin.
Ces règles servent aussi à étiqueter les données simulées (voir generer_donnees.py).
"""
import json
from .config import CATALOGUE_PATH

CATALOGUE = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
PALIERS = [f["debit_mbps"] for f in CATALOGUE["forfaits"]]   # [50, 100, 200, 300, 500, 1000]

# Les colonnes que le modèle utilise (= les réponses du questionnaire)
COLONNES = ["nb_personnes", "nb_appareils", "streaming", "gaming",
            "teletravail", "nb_pieces"]


def besoin_mbps(r: dict) -> float:
    """Estime le débit dont le foyer a besoin, avec 20 % de marge."""
    besoin = (
        4 * r["nb_appareils"]          # chaque appareil connecté en même temps
        + 8 * r["nb_personnes"]        # chaque personne
        + 30 * r["streaming"]          # vidéo HD / Netflix / YouTube
        + 50 * r["gaming"]             # jeux en ligne
        + 30 * r["teletravail"]        # visio, cours en ligne
    )
    return besoin * 1.2


def palier_par_regles(r: dict) -> int:
    """Le plus petit palier qui couvre le besoin estimé."""
    b = besoin_mbps(r)
    for p in PALIERS:
        if p >= b:
            return p
    return PALIERS[-1]


def equipement_pour(nb_pieces: int) -> str:
    """La box couvre bien environ 2 pièces. Au-delà : répéteur ou FTTR."""
    en_plus = nb_pieces - 2
    if en_plus <= 0:
        return "aucun"
    if en_plus == 1:
        return "repeteur"
    return f"fttr_{min(en_plus, 4)}"


def prix_actuel(debit: int, promo: bool = True) -> int:
    f = next(f for f in CATALOGUE["forfaits"] if f["debit_mbps"] == debit)
    return f["prix_promo"] if (promo and f["prix_promo"]) else f["prix"]


def meilleur_rapport(debit: int, promo: bool = True) -> int:
    """Si un palier supérieur coûte le même prix ou moins, on le prend.
    Ex. : sans la promo, 50 Mb/s et 100 Mb/s coûtent tous les deux 15 000."""
    i = PALIERS.index(debit)
    for p in PALIERS[i + 1:]:
        if prix_actuel(p, promo) <= prix_actuel(debit, promo):
            debit = p
    return debit
