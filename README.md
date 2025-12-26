# 🚀 Pump Discover

Echtzeit-Erkennung neuer Pump.fun Tokens mit WebSocket-Relay, n8n-Integration und Streamlit UI.

## 📋 Schnellstart

```bash
# 1. Umgebungsvariablen einrichten
cp .env.example .env
# Bearbeite .env mit deinen Werten (optional - kann auch über UI gemacht werden)

# 2. Services starten
docker compose up -d

# 3. Services öffnen
# Streamlit UI: http://localhost:8501
# API Health-Check: http://localhost:8000/health
# Prometheus Metrics: http://localhost:8000/metrics
```

## 🔌 Port-Konfiguration

Die folgenden Ports werden standardmäßig nach außen geleitet:

| Service | Externer Port | Interner Port | Endpoint |
|---------|---------------|---------------|----------|
| **Streamlit UI** | 8501 | 8501 | http://localhost:8501 |
| **API & Metrics** | 8000 | 8000 | http://localhost:8000 |

**Ports anpassen:**
Die Ports können über Umgebungsvariablen in der `.env` Datei angepasst werden:
```bash
RELAY_PORT=8000    # API & Metrics Port
UI_PORT=8501       # Streamlit UI Port
```

## 📚 Dokumentation

- **[ANLEITUNG.md](ANLEITUNG.md)** - Vollständige Setup-Anleitung
- **[DATEN_MAPPING.md](DATEN_MAPPING.md)** - WebSocket → SQL Mapping (für n8n)
- **[PROJEKT_STRUKTUR.md](PROJEKT_STRUKTUR.md)** - Detaillierte Projektstruktur
- **[API Dokumentation](api/swagger.yaml)** - OpenAPI/Swagger Spezifikation
- **[SQL Schema](sql/schema.sql)** - Datenbankschema
- **[docs/](docs/)** - Zusätzliche Dokumentation (Schema-Vergleiche, etc.)

## 🏗️ Projektstruktur

```
pump-discover/
├── relay/              # Python Relay Service
│   ├── main.py        # Haupt-Service
│   └── Dockerfile     # Relay Container
├── ui/                 # Streamlit UI
│   ├── app.py         # UI Anwendung
│   └── Dockerfile     # UI Container
├── sql/                # Datenbankschema
│   ├── schema.sql     # Tabellen-Schema
│   └── views.sql      # Views für Berechnungen
├── api/                # API Dokumentation
│   └── swagger.yaml   # OpenAPI/Swagger Spezifikation
├── docs/               # Zusätzliche Dokumentation
│   ├── websocket_schema_vergleich.md
│   └── SCHEMA_UEBERSICHT.md
├── scripts/            # Test- und Utility-Scripts
│   ├── test_websocket.py
│   ├── test_metadata.py
│   └── check_open_market_cap.py
├── config/             # Konfigurationsdateien
├── docker-compose.yml # Docker Compose Setup
├── .env.example       # Beispiel-Umgebungsvariablen (wird beim ersten Start erstellt)
├── .gitignore         # Git Ignore Rules
├── ANLEITUNG.md       # Vollständige Anleitung
├── DATEN_MAPPING.md   # WebSocket → SQL Daten-Mapping (für n8n)
└── README.md          # Diese Datei
```

## 🔧 Features

- ✅ WebSocket-Relay für Pump.fun Tokens
- ✅ n8n-Integration für Filterung
- ✅ Streamlit UI für Management
- ✅ Prometheus Metrics
- ✅ Health-Checks
- ✅ Konfigurierbare Filter
- ✅ Service-Neustart über UI
- ✅ Live-Logs und Metriken

## 📊 Datenfluss

```
Pump.fun WebSocket → Python Relay → n8n (Filterung) → Datenbank
```

## 🛠️ Technologie-Stack

- **Python 3.11** - Relay Service
- **Streamlit** - Web UI
- **Docker Compose** - Container-Orchestrierung
- **Prometheus** - Metriken
- **aiohttp/websockets** - Asynchrone WebSocket-Kommunikation

## 📡 API Endpoints

Der Relay-Service bietet folgende HTTP-Endpoints:

### Health Check
```bash
GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "ws_connected": true,
  "n8n_available": true,
  "uptime_seconds": 3600,
  "total_coins": 150,
  "total_batches": 15,
  "last_coin_ago": 5,
  "last_message_ago": 2,
  "reconnect_count": 0,
  "last_error": null
}
```

### Prometheus Metrics
```bash
GET http://localhost:8000/metrics
```

Gibt Prometheus-kompatible Metriken im Text-Format zurück.

**Wichtige Metriken:**
- `pumpfun_coins_received_total` - Gesamt empfangene Coins
- `pumpfun_coins_sent_total` - Gesamt gesendete Coins
- `pumpfun_coins_filtered_total` - Gefilterte Coins (nach Grund)
- `pumpfun_batches_sent_total` - Gesamt gesendete Batches
- `pumpfun_ws_reconnects_total` - WebSocket Reconnects
- `pumpfun_ws_connected` - WebSocket Verbindungsstatus (1=connected)
- `pumpfun_n8n_available` - n8n Verfügbarkeit (1=available)
- `pumpfun_buffer_size` - Aktuelle Buffer-Größe
- `pumpfun_uptime_seconds` - Uptime in Sekunden

Siehe [api/swagger.yaml](api/swagger.yaml) für die vollständige API-Dokumentation.

## 📝 Lizenz

Siehe LICENSE Datei (falls vorhanden).

