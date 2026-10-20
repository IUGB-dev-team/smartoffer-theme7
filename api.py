"""
Le serveur que l'application mobile appelle.

Lancer :  uvicorn api:app --reload
Tester :  ouvrir http://127.0.0.1:8000/docs dans le navigateur
"""
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
from recommander import recommander
from ajustement import ajuster

app = FastAPI(title="Fibre SmartOffer", version="0.1")


class Questionnaire(BaseModel):
    nb_personnes: int = Field(ge=1, le=15)
    nb_appareils: int = Field(ge=1, le=50)
    streaming: bool = False
    gaming: bool = False
    teletravail: bool = False
    nb_pieces: int = Field(ge=1, le=12)
    budget: Optional[int] = None
    eligible: bool = True


class Usage(BaseModel):
    debit_actuel: int
    jours_observes: int
    taux_pointe_moyen: float
    jours_satures: int
    pieces_signal_faible: int = 0
    appareils_max: int = 0


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
