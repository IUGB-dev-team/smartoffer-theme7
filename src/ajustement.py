"""
ÉTAPE 2 — L'ajustement avec l'usage réel (données du diagnostic, thème 3).

Après quelques semaines, on compare ce que le client consomme vraiment
à ce qu'il paie, et on ajuste DANS LES DEUX SENS.
Les noms des champs sont à caler avec la personne du thème 3.
"""
from .regles import PALIERS, prix_actuel

SEUIL_SATURE = 0.85      # utilise plus de 85 % du débit aux heures de pointe
SEUIL_SOUS_UTILISE = 0.30
JOURS_MIN = 14           # sur au moins 2 semaines, pour ne pas réagir à un seul jour


def ajuster(debit_actuel: int, usage: dict) -> dict:
    """
    usage = {
      "jours_observes": 21,
      "taux_pointe_moyen": 0.92,     # débit utilisé / débit souscrit, à 20h-23h
      "jours_satures": 16,           # jours où le taux a dépassé SEUIL_SATURE
      "pieces_signal_faible": 2,     # pièces où le Wi-Fi est faible
      "appareils_max": 14,
    }
    """
    if usage["jours_observes"] < JOURS_MIN:
        return {"action": "attendre", "message": "Pas encore assez de données."}

    i = PALIERS.index(debit_actuel)
    taux = usage["taux_pointe_moyen"]

    # Débit bon mais Wi-Fi faible → équipement, PAS un forfait plus cher
    if usage.get("pieces_signal_faible", 0) > 0 and taux < SEUIL_SATURE:
        equip = "répéteur" if usage["pieces_signal_faible"] == 1 else "kit FTTR"
        return {"action": "equipement",
                "message": f"Votre débit suffit, mais le Wi-Fi est faible dans "
                           f"{usage['pieces_signal_faible']} pièce(s). Un {equip} réglera ça."}

    # Saturé la plupart des jours → offre supérieure
    if taux >= SEUIL_SATURE and usage["jours_satures"] >= usage["jours_observes"] / 2 and i < len(PALIERS) - 1:
        nouveau = PALIERS[i + 1]
        return {"action": "monter", "nouveau_debit": nouveau,
                "message": f"Votre connexion est saturée le soir ({usage['appareils_max']} appareils "
                           f"connectés). Passez à {nouveau} Mb/s pour "
                           f"{prix_actuel(nouveau) - prix_actuel(debit_actuel):+} FCFA/mois."}

    # Sous-utilisé → offre moins chère (c'est ça qui crée la confiance)
    if taux <= SEUIL_SOUS_UTILISE and i > 0:
        nouveau = PALIERS[i - 1]
        economie = prix_actuel(debit_actuel) - prix_actuel(nouveau)
        if economie > 0:
            return {"action": "descendre", "nouveau_debit": nouveau,
                    "message": f"Vous utilisez peu votre forfait. {nouveau} Mb/s vous suffit "
                               f"et vous économisez {economie} FCFA/mois."}

    return {"action": "garder", "message": "Votre offre est parfaitement adaptée à votre foyer."}


if __name__ == "__main__":
    print(ajuster(200, dict(jours_observes=21, taux_pointe_moyen=0.92, jours_satures=16, pieces_signal_faible=0, appareils_max=14)))
    print(ajuster(300, dict(jours_observes=21, taux_pointe_moyen=0.18, jours_satures=0, pieces_signal_faible=0, appareils_max=4)))
    print(ajuster(200, dict(jours_observes=21, taux_pointe_moyen=0.55, jours_satures=2, pieces_signal_faible=2, appareils_max=8)))
    print(ajuster(200, dict(jours_observes=21, taux_pointe_moyen=0.60, jours_satures=1, pieces_signal_faible=0, appareils_max=9)))
