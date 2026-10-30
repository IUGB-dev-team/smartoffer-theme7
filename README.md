# Fibre SmartOffer — Thème 7

**Concours Moov Application 2026 · IUGB**

Une IA qui recommande à chaque client l'offre fibre Moov adaptée à son foyer, avec le bon équipement Wi-Fi et une phrase qui explique pourquoi.

Ce module s'intègre à l'application principale de l'équipe (basée sur le diagnostic du thème 3).

---

## Ce que fait l'IA

1. **Démarrage à froid** : un nouveau client répond à 6 questions simples (personnes, appareils, streaming, jeu en ligne, télétravail, nombre de pièces). L'IA lui propose tout de suite une offre.
2. **Ajustement** : après quelques semaines, les données d'usage du diagnostic (thème 3) permettent d'ajuster l'offre **dans les deux sens** : offre supérieure si la connexion est saturée, offre moins chère si elle est sous-utilisée, ou équipement (répéteur, FTTR) si c'est le Wi-Fi qui est faible.
3. **Parrainage (thème 5)** : un client satisfait reçoit un code à partager. Son filleul s'inscrit avec le code, reçoit son offre personnalisée (grâce au moteur du thème 7), et s'il reste abonné 3 mois, les deux gagnent 1 mois offert.
4. **Cas particuliers** :
   - client non éligible à la fibre → Box 4G ;
   - offre idéale au-dessus du budget → meilleure offre abordable, en le disant honnêtement au client.

---

## Organisation du projet

```
smartoffer-theme7/
├── data/
│   ├── catalogue.json          # toutes les offres fibre Moov (débits, prix, équipements, Box 4G)
│   ├── foyers_simules.csv      # les 5 000 foyers simulés
│   ├── foyers_simules.xlsx     # les mêmes foyers + la répartition des offres, pour Excel
│   └── zones_eligibles.json    # communes couvertes par la fibre (liste simulée pour la démo)
├── models/
│   └── modele_smartoffer.joblib  # le modèle entraîné
├── src/                        # la logique de l'IA
│   ├── config.py               # les chemins du projet
│   ├── regles.py               # version 1 : règles simples (besoin en débit, équipement)
│   ├── generer_donnees.py      # crée les foyers simulés
│   ├── entrainer_modele.py     # entraîne la régression logistique
│   ├── recommander.py          # le moteur complet : offre + équipement + explication + confiance
│   ├── ajustement.py           # ajuste l'offre avec les données d'usage du diagnostic
│   └── parrainage.py           # thème 5 : codes, filleuls, anti-triche, récompenses
├── server/
│   ├── api.py                  # le serveur FastAPI appelé par l'application
│   └── static/demo.html        # la page de démo (questionnaire, ajustement, parrainage)
├── tests/
│   ├── test_api.py             # 10 tests de la recommandation et de l'ajustement
│   └── test_parrainage.py      # 7 tests du parrainage
├── requirements.txt
└── pytest.ini
```

---

## Installation

Il faut Python 3.10 ou plus.

```
pip install -r requirements.txt
```

> Le modèle doit être entraîné avec la **même version de scikit-learn** que celle qui l'utilise. La version est fixée dans `requirements.txt` (1.6.1).

---

## Utilisation

Toutes les commandes se lancent **depuis la racine du projet** :

```
python -m src.generer_donnees      # 1. crée les 5 000 foyers simulés
python -m src.entrainer_modele     # 2. entraîne le modèle et affiche sa précision
python -m src.recommander          # 3. teste le moteur sur 6 exemples de foyers
pytest                             # 4. lance les 18 tests automatiques
uvicorn server.api:app --reload    # 5. lance le serveur
```

Ensuite, ouvrir dans le navigateur :
- **http://127.0.0.1:8000/demo** : la page de démo, pour tester comme un vrai client (recommandation, ajustement, parrainage) ;
- **http://127.0.0.1:8000/docs** : la documentation technique de l'API.

Pour qu'un coéquipier sur le même Wi-Fi appelle le serveur : `uvicorn server.api:app --host 0.0.0.0 --port 8000`, puis utiliser l'adresse IPv4 de l'ordinateur (`ipconfig`).

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

### Parrainage (thème 5)

| Adresse | Rôle |
|---|---|
| `POST /parrainage/code` | Le client (`nom`, `telephone`) reçoit son code, son lien et un message à partager sur WhatsApp |
| `POST /parrainage/inscription` | Le filleul s'inscrit avec le `code`, son `nom`, `telephone`, `commune` et ses réponses au `questionnaire` → il reçoit son offre personnalisée |
| `POST /parrainage/filleul/{id}/avancer` | Démo : fait passer le filleul à l'étape suivante (inscrit → abonné → actif 3 mois) |
| `GET /parrainage/{code}/filleuls` | Le tableau de bord « Mes filleuls » : filleuls, statuts, mois offerts gagnés |

Règles :
- **Anti-triche** : impossible de se parrainer soi-même, ou d'être parrainé deux fois avec le même numéro.
- **Zone fibre** : si la commune du filleul n'est pas couverte, il reçoit la Box 4G au lieu d'être perdu (liste de communes simulée).
- **Récompense** : 1 mois offert pour les deux, seulement quand le filleul est resté abonné 3 mois.
- Les données sont stockées dans une base SQLite (`data/parrainage.db`), créée automatiquement.

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
