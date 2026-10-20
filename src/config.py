"""Les chemins du projet, au même endroit pour tous les fichiers."""
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]      # dossier du projet
DATA = RACINE / "data"
MODELS = RACINE / "models"

CATALOGUE_PATH = DATA / "catalogue.json"
FOYERS_PATH = DATA / "foyers_simules.csv"
MODELE_PATH = MODELS / "modele_smartoffer.joblib"
