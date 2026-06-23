# Tests Automatisés et CI/CD Agentique avec LangGraph

![CI](https://github.com/USER/REPO/actions/workflows/ci-agent.yml/badge.svg)

## Objectif

Ce projet est le support d'un atelier consacré à l'industrialisation d'un agent IA. Il montre comment construire un agent LangGraph capable d'interroger une API externe, de produire une réponse exploitable, de gérer ses défaillances grâce à une Dead Letter Queue (DLQ) locale et d'être sécurisé par des tests métier exécutés en CI/CD.

L'objectif n'est pas seulement de faire fonctionner l'agent : il s'agit de rendre son comportement observable, testable et reproductible avant chaque livraison.

## Architecture

```text
User Input -> LangGraph -> API externe -> Router -> Success Answer ou DLQ Fallback
```

L'API externe utilisée est Wikipédia. Toute erreur HTTP, timeout ou exception est normalisée puis routée vers la DLQ locale `data/dlq_messages.jsonl`.

## Fonctionnement du graphe

Le workflow est composé des nœuds suivants :

- `prepare_input` : nettoie l'entrée utilisateur et produit `normalized_input`.
- `call_api_node` : appelle l'API Wikipédia et normalise son résultat (`SUCCESS` ou `FAILURE`).
- `route_after_api` : choisit la branche de succès ou la branche DLQ selon le statut de l'API.
- `generate_answer_node` : extrait un résumé exploitable et construit la réponse utilisateur.
- `validate_answer_node` : valide la réponse (non vide, au moins 20 caractères, sans `None` ni `NaN`).
- `send_to_dlq_node` : persiste l'échec dans la DLQ et prépare une réponse de repli.
- `final_response_node` : retourne un objet final uniforme pour l'API ou l'appelant Python.

## Installation locale

Python 3.11 est la version cible du projet.

```bash
python -m venv .venv
```

Activez ensuite l'environnement virtuel selon votre système :

```bash
# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\activate
```

Installez les dépendances :

```bash
pip install -r requirements.txt
```

## Exécution de l'agent

Pour exécuter rapidement le workflow avec une question de démonstration :

```bash
python -m app.graph
```

## Exécution de l'API

L'agent peut également être exposé via FastAPI :

```bash
uvicorn app.server:app --host 127.0.0.1 --port 8000
```

Une fois le serveur lancé, appelez `POST /agent/run` avec :

```json
{"input": "Where Morocco is located?"}
```

La supervision est disponible avec `GET /health`.

## Exécution des tests

Exécutez la suite complète :

```bash
pytest -v
```

Générez aussi un rapport HTML de soutenance :

```bash
pytest -v --html=reports/report.html --self-contained-html
```

Le rapport est produit dans `reports/report.html` et est ignoré par Git.

## CI/CD GitHub Actions

La pipeline **Agentic LangGraph CI Pipeline** s'exécute automatiquement à chaque `push` et chaque `pull request` vers les branches `main` et `master`.

Elle installe Python 3.11 et les dépendances, lance les tests, génère le rapport HTML puis le publie comme artifact GitHub Actions. Remplacez `USER/REPO` dans le badge situé en tête de ce document par le chemin de votre dépôt GitHub.

## Mocks utilisés

Les tests ne contactent jamais Internet. Ils utilisent `monkeypatch` pour simuler les comportements suivants :

- Mock API success : résumé Wikipédia valide et réponse conforme.
- Mock API 503 : indisponibilité de service et routage vers la DLQ.
- Mock API 404 : ressource absente et réponse de repli.
- Mock timeout : expiration de délai et routage contrôlé.
- Mock payload invalide : absence de résumé, résumé vide ou contenu non conforme (`None`, `NaN`).
- Mock DLQ locale : écriture isolée dans `tmp_path`, sans modifier les données réelles du projet.

## Livrables

- Code LangGraph : workflow typé, modulaire et résilient.
- Suite de tests : plus de 20 cas métier paramétrés.
- Rapport pytest HTML : résultat de l'exécution de test exploitable en soutenance.
- Pipeline GitHub Actions : validation automatique du projet à chaque changement.
- Documentation des mocks : scénarios de succès, d'échec API, de timeout, de payload invalide et de DLQ.
