# 📁 Projektstruktur - Pump Discover

## 🗂️ Übersicht

```
pump-discover/
├── 📄 README.md                    # Haupt-README mit Schnellstart
├── 📄 ANLEITUNG.md                 # Vollständige Setup-Anleitung
├── 📄 DATEN_MAPPING.md             # WebSocket → SQL Mapping (für n8n)
├── 📄 PROJEKT_STRUKTUR.md          # Diese Datei
│
├── 🐳 docker-compose.yml           # Docker Compose Konfiguration
├── 📝 .gitignore                   # Git Ignore Rules
│
├── 🔧 relay/                        # Python Relay Service
│   ├── main.py                    # Haupt-Service (WebSocket → n8n)
│   └── Dockerfile                 # Relay Container
│
├── 🖥️ ui/                          # Streamlit UI
│   ├── app.py                     # Web-Interface für Konfiguration & Monitoring
│   └── Dockerfile                  # UI Container
│
├── 🗄️ sql/                         # Datenbankschema
│   ├── schema.sql                 # Tabellen-Schema (discovered_coins)
│   └── views.sql                  # SQL Views für Berechnungen
│
├── 📡 api/                         # API Dokumentation
│   └── swagger.yaml               # OpenAPI/Swagger Spezifikation
│
├── 📚 docs/                        # Zusätzliche Dokumentation
│   ├── README.md                  # Dokumentations-Übersicht
│   ├── websocket_schema_vergleich.md
│   └── SCHEMA_UEBERSICHT.md
│
├── 🔬 scripts/                      # Test- und Utility-Scripts
│   ├── README.md                  # Scripts-Übersicht
│   ├── test_websocket.py          # WebSocket Test
│   ├── test_metadata.py           # Metadata Test
│   └── check_open_market_cap.py   # Open Market Cap Check
│
└── ⚙️ config/                      # Konfigurationsdateien
    └── config.yaml                # UI-Konfiguration (wird automatisch erstellt)
```

## 📋 Datei-Beschreibungen

### Root-Dateien

- **README.md** - Haupt-README mit Schnellstart, Features und API-Dokumentation
- **ANLEITUNG.md** - Vollständige Setup-Anleitung mit Troubleshooting
- **DATEN_MAPPING.md** - Detailliertes Mapping zwischen WebSocket-Daten und SQL-Schema (wichtig für n8n)
- **docker-compose.yml** - Docker Compose Konfiguration für alle Services
- **.gitignore** - Git Ignore Rules für Environment-Dateien, Configs, etc.

### Services

#### relay/
- **main.py** - Python Relay Service, der:
  - WebSocket-Verbindung zu Pump.fun aufbaut
  - Neue Token-Erstellungen empfängt
  - Filterung durchführt (Bad Names, Spam-Burst)
  - Batches an n8n sendet
  - Health-Check und Prometheus Metrics bereitstellt
- **Dockerfile** - Container für Relay Service

#### ui/
- **app.py** - Streamlit Web-Interface mit:
  - Dashboard mit Live-Status
  - Konfigurations-Management
  - Log-Viewer
  - Metriken-Anzeige
  - Service-Neustart-Funktion
- **Dockerfile** - Container für Streamlit UI

### Datenbank

#### sql/
- **schema.sql** - Haupt-Schema für `discovered_coins` Tabelle
- **views.sql** - SQL Views für berechnete Metriken (USD-Konvertierung, Graduierung, etc.)

### Dokumentation

#### api/
- **swagger.yaml** - OpenAPI 3.0.3 Spezifikation für Health-Check und Metrics Endpoints

#### docs/
- **websocket_schema_vergleich.md** - Vergleich zwischen WebSocket-Daten und SQL-Schema
- **SCHEMA_UEBERSICHT.md** - Detaillierte Übersicht über das Datenbankschema

### Scripts

#### scripts/
- **test_websocket.py** - Test-Script für WebSocket-Verbindung
- **test_metadata.py** - Test-Script für Metadata-URI-Extraktion
- **check_open_market_cap.py** - Utility-Script für Open Market Cap Prüfung

### Konfiguration

#### config/
- **config.yaml** - Wird automatisch von der Streamlit UI erstellt und verwaltet
- **.env** - Wird automatisch von der Streamlit UI erstellt (nicht in Git)

## 🔄 Datenfluss

```
Pump.fun WebSocket
    ↓
relay/main.py (Filterung, Batching)
    ↓
n8n Webhook (weitere Filterung, Metadata-Extraktion)
    ↓
PostgreSQL Datenbank (discovered_coins Tabelle)
```

## 🚀 Schnellstart

1. **Projekt klonen/kopieren**
2. **Services starten:**
   ```bash
   docker compose up -d
   ```
3. **UI öffnen:**
   - http://localhost:8501
4. **n8n Webhook konfigurieren** (über UI)
5. **Service neu starten** (über UI)

## 📚 Weitere Informationen

- Siehe [README.md](README.md) für Features und API-Dokumentation
- Siehe [ANLEITUNG.md](ANLEITUNG.md) für detaillierte Setup-Anleitung
- Siehe [DATEN_MAPPING.md](DATEN_MAPPING.md) für n8n Workflow-Mapping

