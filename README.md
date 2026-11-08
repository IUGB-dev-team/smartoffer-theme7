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
pytest                             # 4. lance les 21 tests automatiques
uvicorn server.api:app --reload    # 5. lance le serveur
```

Ensuite, ouvrir dans le navigateur :
- **http://127.0.0.1:8000/demo** : la page de démo, pour tester comme un vrai client (recommandation, ajustement, parrainage) ;
- **http://127.0.0.1:8000/docs** : la documentation technique de l'API.

Pour qu'un coéquipier sur le même Wi-Fi appelle le serveur : `uvicorn server.api:app --host 0.0.0.0 --port 8000`, puis utiliser l'adresse IPv4 de l'ordinateur (`ipconfig`).

---

## L'API

### `GET /offres`

Renvoie tout le catalogue : les 6 forfaits fibre (débit, prix, prix promo, avantages mobile), les équipements (répéteur, kits FTTR) et la Box 4G. À utiliser pour afficher la grille des prix dans l'app, au lieu de recopier les prix à la main.

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
  "explication": "Pour 4 personnes, 12 appareils, streaming et télétravail, il faut environ 168 Mb/s : le 200 Mb/s suffit.",
  "alerte_budget": null,
  "offre_superieure": null,
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

## Pour l'équipe : intégrer dans l'application

Ce module fournit l'IA et l'API. Les écrans de l'application sont faits par l'équipe front-end (React Native). Voici comment s'en servir.

### Deux façons de choisir son offre

Proposer deux boutons au client :

| Bouton | Ce qui se passe | Adresse à appeler |
|---|---|---|
| **« Je sais ce que je veux »** | Afficher la grille des prix, le client choisit lui-même son forfait | `GET /offres` |
| **« Aidez-moi à choisir »** | Afficher le questionnaire (6 questions), puis l'offre recommandée par l'IA | `POST /recommandation` |

Dans les deux cas, l'**ajustement** (`POST /ajustement`) fonctionne ensuite : si le client a choisi une offre trop grosse ou trop petite, l'IA le lui signalera après quelques semaines d'usage.

### Budget et offre supérieure

Si l'offre idéale dépasse le `budget` du client, l'API propose la meilleure offre abordable et renvoie :
- `alerte_budget` : une phrase courte qui explique pourquoi (ex. « Avec 20 000 FCFA, on vous propose le 200 Mb/s. L'idéal : 300 Mb/s (+5 000 FCFA/mois). ») ;
- `offre_superieure` : l'offre idéale, avec `debit_mbps`, `prix_mensuel` et `supplement_mensuel`.

Côté application : afficher un bouton **« Passer au 300 Mb/s (+5 000 FCFA / mois) »** quand `offre_superieure` n'est pas `null`. Si le client clique, rappeler `POST /recommandation` sans le budget.

### Grille des prix

- Toujours lire les prix avec `GET /offres` : si Moov change un prix, on modifie seulement `data/catalogue.json` et l'app se met à jour.
- Le 50 Mb/s a un `prix_promo` (7 500 FCFA) : afficher le prix promo barré à côté du prix normal (15 000 FCFA).

### Brancher le diagnostic (thème 3)

Envoyer les 6 données d'usage décrites dans `POST /ajustement` (débit souscrit, jours observés, part du débit utilisée le soir, jours saturés, pièces avec Wi-Fi faible, appareils max). Il faut au moins 14 jours de données pour que l'IA décide.

### Appeler l'API depuis React Native

```javascript
const reponse = await fetch(`${API}/recommandation`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ nb_personnes: 4, nb_appareils: 12, streaming: true, teletravail: true, nb_pieces: 4 }),
});
const offre = await reponse.json();   // offre.debit_mbps, offre.explication, offre.confiance…
```

`API` = l'adresse du serveur. Sur un téléphone, `127.0.0.1` ne marche pas : utiliser l'adresse IPv4 de l'ordinateur qui fait tourner le serveur (même Wi-Fi, avec `--host 0.0.0.0`), ou une adresse en ligne si le serveur est déployé.

### Tester sans l'application

La page **`/demo`** permet de tout essayer dans le navigateur : recommandation, ajustement (données simulées) et parrainage.

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

---

## Mise en ligne de la démo

- **Render** fait tourner l'API Python. La configuration est dans `render.yaml`.
- **Netlify** affiche la page démo et transmet les appels à Render. La configuration est dans `netlify.toml`.

Si l'adresse Render n'est pas `smartoffer-api.onrender.com`, il faut la remplacer dans `netlify.toml`.

Sur le plan gratuit de Render, le serveur s'endort après 15 minutes sans visite. Le premier appel le réveille, ce qui prend environ 1 minute.
