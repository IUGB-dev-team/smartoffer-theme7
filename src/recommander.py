"""
Le moteur complet : réponses du questionnaire → offre + équipement + explication.
C'est cette fonction que le serveur (server/api.py) appelle.
Tester (depuis la racine) :  python -m src.recommander
"""
import joblib
import pandas as pd
from .config import MODELE_PATH
from .regles import (CATALOGUE, COLONNES, PALIERS, besoin_mbps, palier_par_regles,
                    equipement_pour, prix_actuel, meilleur_rapport)

MODELE = joblib.load(MODELE_PATH) if MODELE_PATH.exists() else None


def _fcfa(n: int) -> str:
    """15000 → '15 000'"""
    return f"{n:,}".replace(",", " ")


def _liste(mots: list) -> str:
    """['a', 'b', 'c'] → 'a, b et c'"""
    return mots[0] if len(mots) == 1 else ", ".join(mots[:-1]) + " et " + mots[-1]


def recommander(r: dict, promo: bool = True) -> dict:
    # 1. Pas éligible à la fibre → on ne perd pas le client : Box 4G
    if not r.get("eligible", True):
        box = CATALOGUE["hors_fibre"]
        return {"type": "hors_fibre", "offre": box["nom"], "prix_mensuel": box["prix"],
                "explication": "Votre adresse n'est pas encore couverte par la fibre. "
                               "La Box 4G vous connecte dès aujourd'hui, sans installation."}

    # 2. Le débit : le modèle d'IA s'il existe, sinon les règles
    if MODELE is not None:
        probas = MODELE.predict_proba(pd.DataFrame([r])[COLONNES])[0]
        debit = int(MODELE.classes_[probas.argmax()])
        confiance = float(probas.max())   # à quel point le modèle est sûr de lui
        debit_modele = debit
        methode = "régression logistique"
    else:
        debit = palier_par_regles(r)
        confiance = None
        debit_modele = debit
        methode = "règles"
    if besoin_mbps(r) > 500:          # cas extrême, hors de ce que le modèle a appris
        debit = 1000
    debit = meilleur_rapport(debit, promo)

    # 3. Le budget : si l'offre idéale est trop chère, on propose la meilleure offre abordable,
    #    on explique pourquoi, et on garde l'offre idéale en option (« passer à l'offre supérieure »)
    debit_ideal = debit
    alerte_budget = None
    offre_superieure = None
    budget = r.get("budget")
    if budget and prix_actuel(debit, promo) > budget:
        abordables = [p for p in PALIERS if prix_actuel(p, promo) <= budget]
        if abordables:
            debit = abordables[-1]
            supplement = prix_actuel(debit_ideal, promo) - prix_actuel(debit, promo)
            alerte_budget = (f"Avec {_fcfa(budget)} FCFA, on vous propose le {debit} Mb/s. "
                             f"L'idéal : {debit_ideal} Mb/s (+{_fcfa(supplement)} FCFA/mois).")
            offre_superieure = {"debit_mbps": debit_ideal,
                                "prix_mensuel": prix_actuel(debit_ideal, promo),
                                "supplement_mensuel": supplement}
        else:
            alerte_budget = (f"Aucune offre fibre à {_fcfa(budget)} FCFA. "
                             f"La moins chère : {_fcfa(prix_actuel(PALIERS[0], promo))} FCFA/mois.")

    # La confiance ne vaut que pour l'offre choisie par le modèle :
    # si une règle (budget, 1 Gb/s, meilleur prix) l'a changée, on ne l'affiche pas.
    if debit != debit_modele:
        confiance = None

    # 4. L'équipement selon le nombre de pièces
    equip = equipement_pour(r["nb_pieces"])

    # 5. L'explication : courte, avec le POURQUOI
    besoin = round(besoin_mbps(r))
    n, a = r["nb_personnes"], r["nb_appareils"]
    profil = [f"{n} personne{'s' if n > 1 else ''}", f"{a} appareil{'s' if a > 1 else ''}"]
    profil += [nom for cle, nom in [("streaming", "streaming"), ("gaming", "jeu en ligne"),
                                    ("teletravail", "télétravail")] if r.get(cle)]
    if offre_superieure:
        verdict = f"le {debit} Mb/s peut ralentir le soir"
    elif debit >= besoin:
        verdict = f"le {debit} Mb/s suffit"
    else:
        verdict = f"le {debit} Mb/s est le plus adapté"
    explication = f"Pour {_liste(profil)}, il faut environ {besoin} Mb/s : {verdict}."

    return {
        "type": "fibre",
        "debit_mbps": debit,
        "prix_mensuel": prix_actuel(debit, promo),
        "equipement": CATALOGUE["equipements"][equip],
        "besoin_estime_mbps": round(besoin_mbps(r)),
        "explication": explication,
        "alerte_budget": alerte_budget,
        "offre_superieure": offre_superieure,
        "methode": methode,
        "confiance": round(confiance, 2) if confiance is not None else None,
    }


if __name__ == "__main__":
    exemples = {
        "Étudiant seul": dict(nb_personnes=1, nb_appareils=3, streaming=1, gaming=0, teletravail=1, nb_pieces=1),
        "Couple sans enfant": dict(nb_personnes=2, nb_appareils=5, streaming=1, gaming=0, teletravail=0, nb_pieces=3),
        "Famille de 4 + télétravail": dict(nb_personnes=4, nb_appareils=12, streaming=1, gaming=0, teletravail=1, nb_pieces=4),
        "Grande famille, villa": dict(nb_personnes=7, nb_appareils=18, streaming=1, gaming=1, teletravail=1, nb_pieces=7),
        "Famille, petit budget": dict(nb_personnes=5, nb_appareils=12, streaming=1, gaming=1, teletravail=0, nb_pieces=3, budget=20000),
        "Hors zone fibre": dict(nb_personnes=3, nb_appareils=6, streaming=1, gaming=0, teletravail=0, nb_pieces=2, eligible=False),
    }
    for nom, r in exemples.items():
        res = recommander(r)
        print(f"\n▶ {nom}\n  {res['explication']}")
        if res.get("alerte_budget"):
            print(f"  Budget : {res['alerte_budget']}")
        print(f"  Prix : {res['prix_mensuel']} FCFA/mois")
        if res.get("confiance"):
            print(f"  Confiance du modèle : {res['confiance']:.0%}")
