# Research & Desire — Lockbox MCP Server

Serveur MCP (Model Context Protocol) en mode **HTTP Streamable** exposant l'API [Research & Desire](https://docs.researchanddesire.com/dashboard/api/introduction) — sections **Lockbox Devices**, **Lock Sessions** et **Lock Templates**.

Le serveur tourne dans un conteneur Docker et répond sur la route **`/mcp`**.

---

## Table des matières

1. [Architecture](#architecture)
2. [Outils MCP disponibles](#outils-mcp-disponibles)
3. [Variables d'environnement](#variables-denvironnement)
4. [Lancement rapide avec Docker](#lancement-rapide-avec-docker)
5. [Docker Compose](#docker-compose)
6. [Configuration d'un client MCP](#configuration-dun-client-mcp)
7. [Protocole MCP](#protocole-mcp)
8. [Sécurité](#sécurité)
9. [Structure du projet](#structure-du-projet)

---

## Architecture

```
┌─────────────────┐        JSON-RPC / HTTP         ┌──────────────────────┐
│   Client MCP    │ ─────────────────────────────▶  │  MCP Server (Python) │
│ (Claude, etc.)  │   Bearer MCP_AUTH_TOKEN         │  /mcp                │
└─────────────────┘                                 └──────────┬───────────┘
                                                               │
                                                    Bearer RD_API_TOKEN
                                                               │
                                                               ▼
                                                    ┌──────────────────────┐
                                                    │  R&D Dashboard API   │
                                                    │  /api/v1/lkbx/...    │
                                                    └──────────────────────┘
```

- **Transport** : HTTP Streamable (JSON-RPC 2.0 sur HTTP)
- **Authentification MCP** : Bearer token (`MCP_AUTH_TOKEN`) vérifié par un middleware ASGI
- **Authentification R&D API** : Bearer token (`RD_API_TOKEN`) transmis à chaque appel vers l'API Research & Desire
- **SDK** : [MCP Python SDK](https://pypi.org/project/mcp/) (`FastMCP`)

---

## Outils MCP disponibles

### Lockbox Devices

| Outil | Description | Paramètres |
|-------|-------------|------------|
| `list_lockbox_devices` | Lister tous les appareils Lockbox du compte | `limit` (int, 1-100, défaut 50), `offset` (int, défaut 0) |
| `get_lockbox_device` | Obtenir les détails d'un appareil Lockbox | `device_id` (int, requis) |

### Lock Sessions

| Outil | Description | Paramètres |
|-------|-------------|------------|
| `list_lock_sessions` | Lister toutes les sessions de verrouillage | `limit` (int, 1-100, défaut 50), `offset` (int, défaut 0) |
| `get_lock_session` | Obtenir les détails d'une session par ID | `session_id` (int, requis) |
| `get_active_lock_session` | Obtenir la session active en cours | — |
| `get_latest_lock_session` | Obtenir la session la plus récente | — |
| `lock_or_unlock` | Démarrer un verrouillage ou déverrouiller | `action` ("lock"/"unlock", requis), `lock_settings_id` (int), `keyholder_ids` (list[int]), `target_user_id` (int), `is_test_lock` (bool) |
| `modify_active_lock_session` | Modifier la durée d'une session active | `duration` (int, requis, en secondes), `target_user_id` (int) |

### Lock Templates

| Outil | Description | Paramètres |
|-------|-------------|------------|
| `list_lock_templates` | Lister tous les templates de verrouillage | `limit` (int, 1-100, défaut 50), `offset` (int, défaut 0) |
| `get_lock_template` | Obtenir les détails d'un template par ID | `template_id` (int, requis) |
| `get_active_lock_template` | Obtenir le template de la session active | — |

---

## Variables d'environnement

| Variable | Obligatoire | Description | Valeur par défaut |
|----------|:-----------:|-------------|-------------------|
| `MCP_AUTH_TOKEN` | Recommandé | Token Bearer pour authentifier les clients MCP | *(vide = pas d'auth)* |
| `RD_API_TOKEN` | **Oui** | Token Bearer pour l'API Research & Desire (nécessite un abonnement Ultra) | — |
| `RD_API_BASE_URL` | Non | URL de base de l'API R&D | `https://dashboard.researchanddesire.com/api/v1` |
| `RD_SERVER_PORT` | Non | Port d'écoute du serveur | `3000` |
| `RD_SERVER_HOST` | Non | Adresse d'écoute du serveur | `0.0.0.0` |

> **Note** : Toutes les variables liées à Research & Desire sont préfixées par `RD_`. Le token MCP utilise le nom `MCP_AUTH_TOKEN`.

---

## Lancement rapide avec Docker

### 1. Build de l'image

```bash
docker build -t rd-mcp-server .
```

### 2. Lancement du conteneur

```bash
docker run -d \
  --name rd-mcp-server \
  -p 3000:3000 \
  -e MCP_AUTH_TOKEN="votre-token-mcp-secret" \
  -e RD_API_TOKEN="votre-token-api-rd" \
  -e RD_API_BASE_URL="https://dashboard.researchanddesire.com/api/v1" \
  -e RD_SERVER_PORT="3000" \
  rd-mcp-server
```

### 3. Vérification

```bash
# Envoi d'une requête initialize MCP
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer votre-token-mcp-secret" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": { "name": "test-client", "version": "1.0.0" }
    }
  }'
```

---

## Docker Compose

Un fichier `docker-compose.yml` est fourni. Créez un fichier `.env` à la racine du projet (voir `.env.example`) :

```bash
cp .env.example .env
# Éditez .env avec vos vrais tokens
```

Puis lancez :

```bash
docker compose up -d --build
```

Pour arrêter :

```bash
docker compose down
```

---

## Configuration d'un client MCP

### Claude Desktop / Claude Code

Ajoutez cette configuration dans votre fichier de settings MCP :

```json
{
  "mcpServers": {
    "rd-lockbox": {
      "type": "streamable-http",
      "url": "http://localhost:3000/mcp",
      "headers": {
        "Authorization": "Bearer votre-token-mcp-secret"
      }
    }
  }
}
```

### Exemple d'appel avec curl

```bash
# Lister les outils disponibles
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer votre-token-mcp-secret" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Appeler un outil
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer votre-token-mcp-secret" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "list_lockbox_devices",
      "arguments": { "limit": 10, "offset": 0 }
    }
  }'
```

---

## Protocole MCP

Le serveur implémente le standard **MCP (Model Context Protocol)** complet :

| Méthode | Description |
|---------|-------------|
| `initialize` | Répond à la requête d'initialisation du client avec les capacités du serveur |
| `tools/list` | Liste les 11 outils disponibles avec leurs schémas JSON |
| `tools/call` | Exécute l'outil demandé avec les paramètres fournis et retourne le résultat |

Toutes les réponses suivent le format **JSON-RPC 2.0** :

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { "..." }
}
```

---

## Sécurité

- **Double authentification** : Le serveur MCP est protégé par son propre token (`MCP_AUTH_TOKEN`), indépendant du token de l'API R&D (`RD_API_TOKEN`)
- **Séparation des secrets** : Les tokens sont injectés via des variables d'environnement Docker, jamais dans le code source
- **Pas d'auth = warning** : Si `MCP_AUTH_TOKEN` n'est pas défini, le serveur démarre sans authentification mais affiche un avertissement dans les logs
- **Gestion des erreurs** : Les erreurs de l'API R&D sont capturées et retournées proprement au client MCP (pas de crash serveur)

---

## Structure du projet

```
rd-mcp-server/
├── Dockerfile              # Image Docker (Python 3.12-slim)
├── docker-compose.yml      # Orchestration avec variables d'environnement
├── requirements.txt        # Dépendances Python (mcp, httpx, uvicorn)
├── .env.example            # Modèle de fichier de variables d'environnement
├── .dockerignore           # Fichiers exclus du build Docker
├── README.md               # Cette documentation
└── src/
    ├── __init__.py
    ├── main.py             # Point d'entrée — crée l'app ASGI avec auth middleware
    ├── config.py           # Configuration depuis les variables d'environnement
    ├── auth.py             # Middleware Bearer token pour le serveur MCP
    ├── rd_client.py        # Client HTTP async pour l'API Research & Desire
    └── server.py           # Serveur FastMCP — définition des 11 outils
```
