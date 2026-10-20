# Fibre SmartOffer — Thème 7

**Concours Moov Application 2026 · IUGB**

Une IA qui recommande à chaque client l'offre fibre Moov adaptée à son foyer, avec le bon équipement Wi-Fi et une phrase qui explique pourquoi.

Ce module s'intègre à l'application principale de l'équipe (basée sur le diagnostic du thème 3).

---

## Ce que fait l'IA

1. **Démarrage à froid** : un nouveau client répond à 6 questions simples (personnes, appareils, streaming, jeu en ligne, télétravail, nombre de pièces). L'IA lui propose tout de suite une offre.
2. **Ajustement** : après quelques semaines, les données d'usage du diagnostic (thème 3) permettent d'ajuster l'offre **dans les deux sens** : offre supérieure si la connexion est saturée, offre moins chère si elle est sous-utilisée, ou équipement (répéteur, FTTR) si c'est le Wi-Fi qui est faible.
3. **Cas particuliers** :
   - client non éligible à la fibre → Box 4G ;
   - offre idéale au-dessus du budget → meilleure offre abordable, en le disant honnêtement au client.

---

## Les fichiers

| Fichier | Rôle |
|---|---|
| `catalogue.json` | Toutes les offres fibre Moov (débits, prix, équipements, Box 4G) |
| `regles.py` | Version 1 : règles simples qui estiment le débit nécessaire et choisissent l'équipement |
| `generer_donnees.py` | Crée 5 000 foyers simulés réalistes → `foyers_simules.csv` |
| `entrainer_modele.py` | Entraîne la régression logistique → `modele_smartoffer.joblib` |
| `recommander.py` | Le moteur complet : offre + équipement + explication + alerte budget + confiance |
| `ajustement.py` | Ajuste l'offre à partir des données d'usage du diagnostic |
| `api.py` | Le serveur FastAPI que l'application mobile appelle |
| `requirements.txt` | Les bibliothèques à installer |
| `foyers_simules.xlsx` | Les foyers simulés et la répartition des offres, à ouvrir dans Excel |

---

## Installation

Il faut Python 3.10 ou plus.

```
pip install -r requirements.txt
```

> Le modèle doit être entraîné avec la **même version de scikit-learn** que celle qui l'utilise. La version est fixée dans `requirements.txt` (1.6.1).

---

## Utilisation

Dans l'ordre :

```
python generer_donnees.py      # 1. crée les 5 000 foyers simulés
python entrainer_modele.py     # 2. entraîne le modèle et affiche sa précision
python recommander.py          # 3. teste le moteur sur 6 exemples de foyers
uvicorn api:app --reload       # 4. lance le serveur
```

Ensuite, ouvrir **http://127.0.0.1:8000/docs** dans le navigateur pour tester l'API.

---

## L'API

### `POST /recommandation`

Les réponses du questionnaire → l'offre recommandée.

Exemple d'envoi :
```json
{
  "nb_personnes": 4,
  "nb_appareils": 12,
  "streaming": true,
  "gaming": false,
  "teletravail": true,
  "nb_pieces": 4,
  "budget": null,
  "eligible": true
}
```

Réponse :
```json
{
  "type": "fibre",
  "debit_mbps": 200,
  "prix_mensuel": 20000,
  "equipement": {"nom": "FTTR 1 principal + 2 secondaires", "prix": 167500},
  "explication": "200 Mb/s, car 4 personne(s), 12 appareils, du streaming, du télétravail. Avec 4 pièces, on ajoute : FTTR 1 principal + 2 secondaires.",
  "alerte_budget": null,
  "methode": "régression logistique",
  "confiance": 0.82
}
```

### `POST /ajustement`

Les données d'usage du diagnostic → l'action conseillée (`monter`, `descendre`, `equipement`, `garder` ou `attendre`).

Exemple d'envoi :
```json
{
  "debit_actuel": 200,
  "jours_observes": 21,
  "taux_pointe_moyen": 0.92,
  "jours_satures": 16,
  "pieces_signal_faible": 0,
  "appareils_max": 14
}
```

| Champ | Signification |
|---|---|
| `debit_actuel` | Débit souscrit par le client (Mb/s) |
| `jours_observes` | Nombre de jours de données (au moins 14 pour décider) |
| `taux_pointe_moyen` | Part du débit utilisée le soir (20h-23h), de 0 à 1 |
| `jours_satures` | Nombre de jours où la connexion a dépassé 85 % |
| `pieces_signal_faible` | Nombre de pièces où le Wi-Fi est faible |
| `appareils_max` | Nombre maximum d'appareils connectés en même temps |

---

## Le modèle

- **Type** : régression logistique (classification), avec scikit-learn.
- **Données** : 5 000 foyers simulés, 80 % pour l'entraînement et 20 % pour le test.
- **Précision** : **88,7 %** sur 1 000 foyers jamais vus (un arbre de décision testé en comparaison fait 86 %).
- **Ce qui compte le plus** : jeu en ligne (23 %), nombre d'appareils (21 %), streaming (18 %), nombre de personnes et télétravail (17 % chacun).
- **Pourquoi ce choix** : on a peu de données, et on doit pouvoir expliquer la recommandation au client.

### Limites connues

- Les données sont **simulées**, pas des données réelles de Moov. Le modèle est conçu pour être réentraîné sur les vraies données.
- Le palier **500 Mb/s** est mal reconnu : seulement 56 foyers sur 5 000 en ont besoin.
- Le **1 Gb/s** est géré par une règle (besoin estimé supérieur à 500 Mb/s), pas par le modèle.

---

## Sources des offres

Offres relevées sur [mafibremoov.ci](https://www.mafibremoov.ci/) et [moov-africa.ci](https://www.moov-africa.ci/) le 29/09/2026. Le 50 Mb/s est affiché à 7 500 FCFA en promotion (prix normal : 15 000 FCFA).

---

*Noura, IUGB — Concours Moov Application 2026*
