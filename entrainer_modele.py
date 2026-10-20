"""
VERSION 2 — Le modèle d'IA : une régression logistique.

C'est de la CLASSIFICATION : entrée = profil du foyer, sortie = palier de débit.
Elle donne un poids à chaque réponse et calcule la probabilité de chaque offre.

Lancer :  python entrainer_modele.py   →  crée modele_smartoffer.joblib
"""
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import accuracy_score
from regles import COLONNES

df = pd.read_csv("foyers_simules.csv")
X, y = df[COLONNES], df["offre_mbps"]

# 80 % pour apprendre, 20 % pour tester sur des foyers jamais vus
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

# StandardScaler met toutes les réponses à la même échelle
# (sinon "12 appareils" pèserait plus que "télétravail = 1" juste à cause du chiffre)
modele = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
modele.fit(X_train, y_train)

print(f"Précision : {accuracy_score(y_test, modele.predict(X_test)):.1%} "
      f"(test sur {len(X_test)} foyers jamais vus)")

# Le poids de chaque réponse : plus il est grand, plus la réponse compte
import numpy as np
poids = np.abs(modele[-1].coef_).mean(axis=0)
poids = poids / poids.sum()
print("\nCe qui compte le plus pour le modèle :")
for col, p in sorted(zip(COLONNES, poids), key=lambda t: -t[1]):
    print(f"  {col:<14} {p:.0%}")

# Exemple : la probabilité de chaque offre pour une famille de 4
exemple = pd.DataFrame([dict(nb_personnes=4, nb_appareils=12, streaming=1,
                             gaming=0, teletravail=1, nb_pieces=4)])
print("\nFamille de 4, 12 appareils, streaming + télétravail :")
for offre, proba in zip(modele.classes_, modele.predict_proba(exemple)[0]):
    print(f"  {offre:>4} Mb/s : {proba:.0%}")

print()
joblib.dump(modele, "modele_smartoffer.joblib")
print("Modèle sauvegardé → modele_smartoffer.joblib")
