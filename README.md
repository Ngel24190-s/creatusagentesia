# NosVers Agent Ecosystem

Systeme multi-agent autonome pour [NosVers](https://nosvers.com), ferme familiale agroecologique de lombricompost en Dordogne.

## Agents

| Agent | Fichier | Role |
|-------|---------|------|
| **Content Guardian** | `agents/agent_content.py` | Audit qualite du contenu (grammaire, SEO, voix de marque) |
| **Photo Manager** | `agents/agent_photos.py` | Audit et optimisation de la bibliotheque media WordPress |
| **Social Media Manager** | `agents/agent_social.py` | Generation de posts Instagram, Facebook, TikTok |
| **Orchestrator** | `orchestrator.py` | Coordination des agents, rapports hebdomadaires |

## Installation

```bash
# Cloner le projet
git clone <repo-url>
cd creatusagentesia

# Environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Dependances
pip install -r requirements.txt

# Configuration
cp config.yaml.example config.yaml
# Editer config.yaml avec vos identifiants WordPress
```

## Configuration

Editer `config.yaml` avec :
- **WordPress** : URL du site, utilisateur API, mot de passe d'application
- **SEO** : Mots-cles prioritaires, phrases interdites
- **Email** (optionnel) : SMTP pour envoi du rapport hebdomadaire
- **Buffer** (optionnel) : Token API pour planification automatique des posts

## Utilisation

```bash
# Tester la connexion a l'API WordPress
python orchestrator.py --test

# Lancer tous les agents
python orchestrator.py --run-all

# Lancer un agent specifique
python orchestrator.py --agent content
python orchestrator.py --agent photos
python orchestrator.py --agent social

# Generer le rapport hebdomadaire
python orchestrator.py --report
```

## Workflow

1. **Content Guardian** audite pages, posts et produits WordPress
2. **Photo Manager** audite la bibliotheque media (alt text, noms, orphelins)
3. **Social Media Manager** genere des posts (bloque si corrections en attente)
4. **Orchestrator** coordonne le tout et produit un rapport

### Approbation manuelle

Rien ne se publie automatiquement :
- Les corrections de contenu sont dans `reports/corrections_pending.json`
- Les posts sociaux sont dans `reports/social_queue_*.md`
- Pour appliquer : mettre le `status` sur `"approved"` dans `shared_state.json`

## Cron (production)

```cron
# Audit complet chaque lundi a 6h
0 6 * * 1 cd /path/to/creatusagentesia && /path/to/venv/bin/python orchestrator.py --run-all

# Rapport hebdomadaire chaque dimanche a 20h
0 20 * * 0 cd /path/to/creatusagentesia && /path/to/venv/bin/python orchestrator.py --report
```

## Structure

```
creatusagentesia/
├── orchestrator.py          # Point d'entree principal (CLI)
├── config.yaml              # Configuration (gitignore)
├── config.yaml.example      # Template de configuration
├── shared_state.json        # Etat partage entre agents (gitignore)
├── requirements.txt
├── agents/
│   ├── __init__.py
│   ├── config_loader.py     # Chargement YAML
│   ├── logger.py            # Logging centralise
│   ├── shared_state.py      # Gestion de l'etat partage
│   ├── wp_client.py         # Client WordPress REST API
│   ├── agent_content.py     # Agent 1 — Gardien du Contenu
│   ├── agent_photos.py      # Agent 2 — Gestionnaire des Medias
│   └── agent_social.py      # Agent 3 — Responsable Reseaux Sociaux
├── reports/                 # Rapports generes (gitignore)
├── logs/                    # Logs (gitignore)
├── content_seeds/           # Notes/voix transcrites d'Angel et Africa
└── tests/
    └── test_wp_connection.py
```

## Securite

- Les identifiants sont dans `config.yaml` (jamais commite)
- Les modifications WordPress necessite une approbation manuelle
- Aucune dependance SaaS obligatoire — tourne en local ou sur VPS
