"""
Génère des foyers fictifs mais réalistes, étiquetés avec l'offre adaptée.
Moov ne nous donne pas ses données : on simule, puis le modèle pourra être
réentraîné sur les vraies données plus tard.

Lancer :  python generer_donnees.py   →  crée foyers_simules.csv
"""
import numpy as np
import pandas as pd
from regles import palier_par_regles, PALIERS

rng = np.random.default_rng(42)   # graine fixe = mêmes données à chaque lancement
N = 5000

nb_personnes = rng.choice([1, 2, 3, 4, 5, 6, 7, 8], size=N,
                          p=[.15, .15, .17, .18, .14, .10, .06, .05])
# plus de personnes → plus d'appareils (2 à 3 par personne en moyenne)
nb_appareils = np.clip(np.round(nb_personnes * rng.uniform(1.5, 3.2, N)), 1, 30).astype(int)
streaming = (rng.random(N) < 0.35 + 0.08 * nb_personnes).astype(int)
gaming = (rng.random(N) < 0.10 + 0.04 * nb_personnes).astype(int)
teletravail = (rng.random(N) < 0.35).astype(int)
nb_pieces = np.clip(np.round(nb_personnes * rng.uniform(0.5, 1.2, N)) + 1, 1, 8).astype(int)

df = pd.DataFrame(dict(nb_personnes=nb_personnes, nb_appareils=nb_appareils,
                       streaming=streaming, gaming=gaming,
                       teletravail=teletravail, nb_pieces=nb_pieces))

# L'étiquette = l'offre donnée par nos règles…
df["offre_mbps"] = df.apply(lambda r: palier_par_regles(r.to_dict()), axis=1)

# …avec 10 % de "bruit" : dans la vraie vie, certains foyers prennent
# un palier au-dessus ou en dessous. Ça rend les données plus réalistes.
bruit = rng.random(N) < 0.10
for i in df.index[bruit]:
    j = PALIERS.index(df.at[i, "offre_mbps"]) + rng.choice([-1, 1])
    df.at[i, "offre_mbps"] = PALIERS[int(np.clip(j, 0, len(PALIERS) - 1))]

# Le 1 Gb/s concerne quasiment aucun foyer (usage extrême / bureau) :
# le modèle apprend de 50 à 500 Mb/s, et recommander.py gère le 1 Gb/s par une règle.
df["offre_mbps"] = df["offre_mbps"].clip(upper=500)

df.to_csv("foyers_simules.csv", index=False)
print(f"{N} foyers générés → foyers_simules.csv")
print(df["offre_mbps"].value_counts().sort_index().to_string())
