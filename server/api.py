"""
Le serveur que l'application mobile appelle.

Lancer (depuis la racine du projet) :  uvicorn server.api:app --reload
Tester :  ouvrir http://127.0.0.1:8000/docs dans le navigateur
"""
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.ajustement import ajuster
from src.recommander import recommander
from src.regles import CATALOGUE
from src import parrainage

app = FastAPI(
    title="Fibre SmartOffer",
    description="Recommandation intelligente de l'offre fibre Moov adaptée (thème 7).",
    version="1.0",
)

# Autorise l'app de l'équipe (web ou mobile) à appeler le serveur.
# Pour la démo, toutes les origines sont acceptées ; en production, on listerait les adresses autorisées.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Questionnaire(BaseModel):
    nb_personnes: int = Field(ge=1, le=15, description="Nombre de personnes dans le foyer")
    nb_appareils: int = Field(ge=1, le=50, description="Appareils connectés en même temps")
    streaming: bool = False
    gaming: bool = False
    teletravail: bool = False
    nb_pieces: int = Field(ge=1, le=12, description="Nombre de pièces à couvrir")
    budget: Optional[int] = Field(default=None, description="Budget mensuel en FCFA")
    eligible: bool = Field(default=True, description="Adresse couverte par la fibre")


class NouveauParrain(BaseModel):
    nom: str = Field(min_length=1)
    telephone: str = Field(min_length=8)


class InscriptionFilleul(BaseModel):
    code: str
    nom: str = Field(min_length=1)
    telephone: str = Field(min_length=8)
    commune: str = Field(description="Commune du filleul, pour vérifier la zone fibre")
    questionnaire: Questionnaire


class Usage(BaseModel):
    debit_actuel: int = Field(description="Débit souscrit (Mb/s)")
    jours_observes: int = Field(ge=0)
    taux_pointe_moyen: float = Field(ge=0, le=1, description="Part du débit utilisée le soir")
    jours_satures: int = Field(ge=0)
    pieces_signal_faible: int = Field(default=0, ge=0)
    appareils_max: int = Field(default=0, ge=0)


@app.get("/")
def accueil():
    return {"service": "Fibre SmartOffer", "statut": "ok", "documentation": "/docs", "demo": "/demo"}


@app.get("/demo", include_in_schema=False)
def demo():
    """La page de démo : questionnaire, ajustement et parrainage, dans le navigateur."""
    # no-store : le navigateur recharge toujours la dernière version de la page
    return FileResponse(Path(__file__).parent / "static" / "demo.html", headers={"Cache-Control": "no-store"})


@app.get("/offres")
def get_offres():
    """Tout le catalogue Moov (forfaits, équipements, Box 4G), pour afficher la grille des prix dans l'app."""
    return {cle: valeur for cle, valeur in CATALOGUE.items() if not cle.startswith("_")}


@app.post("/recommandation")
def post_recommandation(q: Questionnaire):
    r = q.model_dump()
    for cle in ("streaming", "gaming", "teletravail"):
        r[cle] = int(r[cle])
    return recommander(r)


@app.post("/ajustement")
def post_ajustement(u: Usage):
    d = u.model_dump()
    return ajuster(d.pop("debit_actuel"), d)


# ---------- Thème 5 : parrainage ----------

def _erreur(e: parrainage.ErreurParrainage):
    raise HTTPException(status_code=400, detail=str(e))


@app.post("/parrainage/code")
def post_code(p: NouveauParrain):
    """Le client satisfait reçoit son code et son lien de parrainage."""
    return parrainage.creer_code(p.nom, p.telephone)


@app.post("/parrainage/inscription")
def post_inscription(i: InscriptionFilleul):
    """Le filleul s'inscrit avec le code et reçoit son offre personnalisée."""
    q = i.questionnaire.model_dump()
    q.pop("eligible", None)
    for cle in ("streaming", "gaming", "teletravail"):
        q[cle] = int(q[cle])
    try:
        return parrainage.inscrire_filleul(i.code, i.nom, i.telephone, i.commune, q)
    except parrainage.ErreurParrainage as e:
        _erreur(e)


@app.post("/parrainage/filleul/{filleul_id}/avancer")
def post_avancer(filleul_id: int):
    """Démo : passe le filleul à l'étape suivante (inscrit → abonné → actif 3 mois)."""
    try:
        return parrainage.avancer_filleul(filleul_id)
    except parrainage.ErreurParrainage as e:
        _erreur(e)


@app.get("/parrainage/{code}/filleuls")
def get_filleuls(code: str):
    """Le tableau de bord « Mes filleuls » du parrain."""
    try:
        return parrainage.mes_filleuls(code)
    except parrainage.ErreurParrainage as e:
        _erreur(e)
