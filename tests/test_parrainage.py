"""
Tests automatiques du parrainage (thème 5).

Chaque test utilise une base de données temporaire, pour ne pas toucher à data/parrainage.db.
"""
import pytest
from fastapi.testclient import TestClient

from server.api import app
from src import parrainage

client = TestClient(app)

QUESTIONNAIRE = {"nb_personnes": 4, "nb_appareils": 12, "streaming": True, "teletravail": True, "nb_pieces": 4}


@pytest.fixture(autouse=True)
def base_temporaire(tmp_path, monkeypatch):
    monkeypatch.setattr(parrainage, "DB_PATH", tmp_path / "test.db")


def nouveau_code(nom="Noura", tel="0707000001"):
    return client.post("/parrainage/code", json={"nom": nom, "telephone": tel}).json()["code"]


def inscrire(code, tel="0505000002", commune="Cocody"):
    return client.post("/parrainage/inscription", json={
        "code": code, "nom": "Awa", "telephone": tel, "commune": commune, "questionnaire": QUESTIONNAIRE})


def test_code_cree_et_stable():
    code = nouveau_code()
    assert code.startswith("MOOV-NOURA-")
    assert nouveau_code() == code          # le même client garde le même code


def test_filleul_recoit_offre_personnalisee():
    res = inscrire(nouveau_code()).json()
    assert res["zone_eligible"] is True
    assert res["offre_personnalisee"]["debit_mbps"] == 200


def test_filleul_hors_zone_recoit_box_4g():
    res = inscrire(nouveau_code(), commune="Korhogo").json()
    assert res["zone_eligible"] is False
    assert res["offre_personnalisee"]["type"] == "hors_fibre"


def test_code_inconnu_refuse():
    assert inscrire("MOOV-FAUX-0000").status_code == 400


def test_auto_parrainage_refuse():
    code = nouveau_code(tel="07 07 00 00 01")
    assert inscrire(code, tel="0707000001").status_code == 400


def test_double_parrainage_refuse():
    code = nouveau_code()
    assert inscrire(code).status_code == 200
    assert inscrire(code).status_code == 400


def test_parcours_complet_et_recompense():
    code = nouveau_code()
    fid = inscrire(code).json()["filleul_id"]
    assert client.post(f"/parrainage/filleul/{fid}/avancer").json()["statut"] == "abonne"
    res = client.post(f"/parrainage/filleul/{fid}/avancer").json()
    assert res["statut"] == "actif_3_mois"
    assert "1 mois offert" in res["recompense"]
    tableau = client.get(f"/parrainage/{code}/filleuls").json()
    assert tableau["nb_filleuls"] == 1 and tableau["recompenses_gagnees"] == 1
