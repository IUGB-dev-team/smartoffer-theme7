"""
Tests automatiques de l'API.

Lancer (depuis la racine du projet) :  pytest
"""
from fastapi.testclient import TestClient

from server.api import app

client = TestClient(app)


def recommandation(**reponses):
    return client.post("/recommandation", json=reponses)


def ajustement(**usage):
    return client.post("/ajustement", json=usage).json()


# ---------- /recommandation ----------

def test_famille_classique():
    res = recommandation(nb_personnes=4, nb_appareils=12, streaming=True, teletravail=True, nb_pieces=4).json()
    assert res["debit_mbps"] == 200
    assert res["prix_mensuel"] == 20000
    assert res["equipement"]["nom"].startswith("FTTR")
    assert res["confiance"] > 0.5


def test_petit_budget():
    res = recommandation(nb_personnes=5, nb_appareils=12, streaming=True, gaming=True,
                         nb_pieces=3, budget=20000).json()
    assert res["prix_mensuel"] <= 20000
    assert res["alerte_budget"] is not None
    # l'offre idéale reste proposée en option, avec le supplément à payer
    sup = res["offre_superieure"]
    assert sup["debit_mbps"] > res["debit_mbps"]
    assert sup["supplement_mensuel"] == sup["prix_mensuel"] - res["prix_mensuel"]


def test_non_eligible_box_4g():
    res = recommandation(nb_personnes=3, nb_appareils=6, nb_pieces=2, eligible=False).json()
    assert res["type"] == "hors_fibre"
    assert "Box 4G" in res["offre"]


def test_usage_extreme_1_gbps():
    res = recommandation(nb_personnes=15, nb_appareils=50, streaming=True, gaming=True,
                         teletravail=True, nb_pieces=10).json()
    assert res["debit_mbps"] == 1000


def test_reponse_invalide_refusee():
    assert recommandation(nb_personnes=0, nb_appareils=5, nb_pieces=2).status_code == 422


# ---------- /ajustement ----------

def test_connexion_saturee_monter():
    res = ajustement(debit_actuel=200, jours_observes=21, taux_pointe_moyen=0.92, jours_satures=16, appareils_max=14)
    assert res["action"] == "monter" and res["nouveau_debit"] == 300


def test_sous_utilise_descendre():
    res = ajustement(debit_actuel=300, jours_observes=21, taux_pointe_moyen=0.18, jours_satures=0)
    assert res["action"] == "descendre" and res["nouveau_debit"] == 200


def test_wifi_faible_equipement():
    res = ajustement(debit_actuel=200, jours_observes=21, taux_pointe_moyen=0.55, jours_satures=2, pieces_signal_faible=2)
    assert res["action"] == "equipement"


def test_offre_adaptee_garder():
    res = ajustement(debit_actuel=200, jours_observes=21, taux_pointe_moyen=0.60, jours_satures=1)
    assert res["action"] == "garder"


def test_trop_tot_attendre():
    res = ajustement(debit_actuel=200, jours_observes=7, taux_pointe_moyen=0.9, jours_satures=5)
    assert res["action"] == "attendre"


def test_page_demo():
    res = client.get("/demo")
    assert res.status_code == 200
    assert "Fibre SmartOffer" in res.text


def test_grille_des_offres():
    res = client.get("/offres").json()
    assert len(res["forfaits"]) == 6
    assert "repeteur" in res["equipements"]
    assert "hors_fibre" in res


def test_budget_trop_petit():
    res = recommandation(nb_personnes=2, nb_appareils=4, nb_pieces=2, budget=5000).json()
    assert "Aucune offre fibre" in res["alerte_budget"]
    assert res["offre_superieure"] is None


def test_explication_donne_le_pourquoi():
    res = recommandation(nb_personnes=4, nb_appareils=12, streaming=True, teletravail=True, nb_pieces=4).json()
    assert "4 personnes" in res["explication"]
    assert "il faut environ" in res["explication"]
