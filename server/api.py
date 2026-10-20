"""
Le serveur que l'application mobile appelle.

Lancer (depuis la racine du projet) :  uvicorn server.api:app --reload
Tester :  ouvrir http://127.0.0.1:8000/docs dans le navigateur
"""
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.ajustement import ajuster
from src.recommander import recommander

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


class Usage(BaseModel):
    debit_actuel: int = Field(description="Débit souscrit (Mb/s)")
    jours_observes: int = Field(ge=0)
    taux_pointe_moyen: float = Field(ge=0, le=1, description="Part du débit utilisée le soir")
    jours_satures: int = Field(ge=0)
    pieces_signal_faible: int = Field(default=0, ge=0)
    appareils_max: int = Field(default=0, ge=0)


@app.get("/")
def accueil():
    return {"service": "Fibre SmartOffer", "statut": "ok", "documentation": "/docs"}


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
