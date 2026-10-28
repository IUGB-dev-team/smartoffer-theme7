"""
THÈME 5 — Le parrainage digital intelligent.

Le parcours d'un filleul :
  1. le parrain (client satisfait) reçoit un code et un lien à partager ;
  2. le filleul s'inscrit avec le code : on vérifie sa zone, on bloque la triche,
     et il reçoit son offre personnalisée (moteur du thème 7) ;
  3. il s'abonne ;
  4. il reste abonné 3 mois → récompense : 1 mois offert pour les deux.

Les données sont stockées dans une petite base SQLite (data/parrainage.db),
qui se crée toute seule au premier lancement.
"""
import json
import secrets
import sqlite3
from datetime import datetime

from .config import DATA
from .recommander import recommander

DB_PATH = DATA / "parrainage.db"
ZONES = json.loads((DATA / "zones_eligibles.json").read_text(encoding="utf-8"))["communes"]

# Les étapes du suivi, dans l'ordre
ETAPES = ["inscrit", "abonne", "actif_3_mois"]
RECOMPENSE = "1 mois offert"


class ErreurParrainage(Exception):
    """Une règle du parrainage n'est pas respectée (code inconnu, triche…)."""


def _connexion():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS parrains (
        code TEXT PRIMARY KEY, nom TEXT, telephone TEXT UNIQUE, cree_le TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS filleuls (
        id INTEGER PRIMARY KEY AUTOINCREMENT, code_parrain TEXT, nom TEXT,
        telephone TEXT UNIQUE, commune TEXT, offre TEXT, statut TEXT, cree_le TEXT)""")
    return con


def _normaliser(tel: str) -> str:
    """Garde seulement les chiffres : '07 07 12 34 56' et '0707123456' sont le même numéro."""
    return "".join(c for c in tel if c.isdigit())


def creer_code(nom: str, telephone: str) -> dict:
    """Donne un code de parrainage au client (le même s'il en a déjà un)."""
    tel = _normaliser(telephone)
    with _connexion() as con:
        existant = con.execute("SELECT code FROM parrains WHERE telephone = ?", (tel,)).fetchone()
        if existant:
            code = existant["code"]
        else:
            prenom = "".join(c for c in nom.split()[0].upper() if c.isalpha())[:8] or "CLIENT"
            code = f"MOOV-{prenom}-{secrets.token_hex(2).upper()}"   # ex. MOOV-NOURA-7K2A
            con.execute("INSERT INTO parrains VALUES (?, ?, ?, ?)",
                        (code, nom, tel, datetime.now().isoformat(timespec="seconds")))
    return {"code": code,
            "lien": f"https://smartoffer.moov.ci/parrainage?code={code}",
            "message_a_partager": f"Rejoins-moi sur la fibre Moov ! Découvre l'offre idéale pour ton foyer "
                                  f"et on gagne tous les deux {RECOMPENSE} : smartoffer.moov.ci/parrainage?code={code}"}


def inscrire_filleul(code: str, nom: str, telephone: str, commune: str, questionnaire: dict) -> dict:
    """Le filleul s'inscrit avec le code : contrôles, puis offre personnalisée."""
    tel = _normaliser(telephone)
    with _connexion() as con:
        parrain = con.execute("SELECT * FROM parrains WHERE code = ?", (code,)).fetchone()
        if not parrain:
            raise ErreurParrainage("Code de parrainage inconnu.")
        # Anti-triche : on ne peut pas se parrainer soi-même, ni être parrainé deux fois
        if tel == parrain["telephone"]:
            raise ErreurParrainage("On ne peut pas se parrainer soi-même.")
        if con.execute("SELECT 1 FROM filleuls WHERE telephone = ?", (tel,)).fetchone():
            raise ErreurParrainage("Ce numéro a déjà été parrainé.")

        # Zone éligible ? (liste simulée pour la démo)
        eligible = commune.strip().lower() in {z.lower() for z in ZONES}
        # L'offre personnalisée vient du moteur du thème 7
        offre = recommander({**questionnaire, "eligible": eligible})

        cur = con.execute("INSERT INTO filleuls (code_parrain, nom, telephone, commune, offre, statut, cree_le) "
                          "VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (code, nom, tel, commune, json.dumps(offre, ensure_ascii=False), "inscrit",
                           datetime.now().isoformat(timespec="seconds")))
    return {"filleul_id": cur.lastrowid, "parrain": parrain["nom"], "zone_eligible": eligible,
            "offre_personnalisee": offre, "statut": "inscrit"}


def avancer_filleul(filleul_id: int) -> dict:
    """Passe le filleul à l'étape suivante (pour la démo : simule l'abonnement puis les 3 mois)."""
    with _connexion() as con:
        f = con.execute("SELECT * FROM filleuls WHERE id = ?", (filleul_id,)).fetchone()
        if not f:
            raise ErreurParrainage("Filleul introuvable.")
        i = ETAPES.index(f["statut"])
        if i < len(ETAPES) - 1:
            con.execute("UPDATE filleuls SET statut = ? WHERE id = ?", (ETAPES[i + 1], filleul_id))
            statut = ETAPES[i + 1]
        else:
            statut = f["statut"]
    recompense = RECOMPENSE if statut == "actif_3_mois" else None
    return {"filleul_id": filleul_id, "statut": statut,
            "recompense": f"{recompense} pour le parrain et le filleul" if recompense else None}


def mes_filleuls(code: str) -> dict:
    """Le tableau de bord « Mes filleuls » du parrain."""
    with _connexion() as con:
        parrain = con.execute("SELECT * FROM parrains WHERE code = ?", (code,)).fetchone()
        if not parrain:
            raise ErreurParrainage("Code de parrainage inconnu.")
        lignes = con.execute("SELECT id, nom, commune, statut, cree_le FROM filleuls "
                             "WHERE code_parrain = ? ORDER BY id", (code,)).fetchall()
    filleuls = [dict(l) for l in lignes]
    gagnes = sum(f["statut"] == "actif_3_mois" for f in filleuls)
    return {"parrain": parrain["nom"], "code": code, "nb_filleuls": len(filleuls),
            "recompenses_gagnees": gagnes,
            "resume": f"{len(filleuls)} filleul(s), {gagnes} mois offert(s) gagné(s)",
            "filleuls": filleuls}
