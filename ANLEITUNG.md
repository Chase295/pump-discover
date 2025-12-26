# 🚀 Pump Discover - Komplette Anleitung

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Voraussetzungen](#voraussetzungen)
3. [Installation](#installation)
4. [Konfiguration](#konfiguration)
5. [Start & Betrieb](#start--betrieb)
6. [Streamlit UI](#streamlit-ui)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Übersicht

Pump Discover ist ein System zur Echtzeit-Erkennung neuer Pump.fun Tokens mit:
- **Python Relay Service**: Empfängt Tokens über WebSocket und sendet sie an n8n
- **Streamlit UI**: Web-Interface für Konfiguration, Monitoring und Management
- **Prometheus Metrics**: Detaillierte Metriken für Monitoring
- **Docker Compose**: Einfache Deployment-Lösung

**Datenfluss:** `Pump.fun WebSocket → Python Relay → n8n (Filterung) → Datenbank`

---

## 📦 Voraussetzungen

### Benötigte Software:
- **Docker** (Version 20.10+)
- **Docker Compose** (Version 2.0+)
- **Git** (optional, für Repository-Clone)

### System-Anforderungen:
- **RAM**: Mindestens 512MB (empfohlen: 1GB+)
- **CPU**: 1 Core (empfohlen: 2+ Cores)
- **Netzwerk**: Internet-Verbindung für WebSocket und n8n

### Prüfen der Installation:
```bash
# Docker Version prüfen
docker --version

# Docker Compose Version prüfen
docker compose version

# Docker Service Status prüfen
docker info
```

---

## 🔧 Installation

### 1. Projekt-Verzeichnis erstellen

```bash
# Erstelle Projekt-Verzeichnis
mkdir -p ~/pump-discover
cd ~/pump-discover
```

### 2. Projekt-Dateien kopieren

Kopiere alle Projekt-Dateien in das Verzeichnis:
- `relay/` - Python Relay Service
- `ui/` - Streamlit UI
- `docker-compose.yml` - Docker Compose Konfiguration
- `.env.example` - Beispiel-Umgebungsvariablen

### 3. Umgebungsvariablen einrichten

```bash
# Kopiere Beispiel-Datei
cp .env.example .env

# Bearbeite .env Datei mit deinen Werten
nano .env  # oder vim, code, etc.
```

**Wichtige Einstellungen:**
- `N8N_WEBHOOK_URL`: Deine n8n Webhook-URL
- `RELAY_PORT`: Port für Relay Health/Metrics (Standard: 8000)
- `UI_PORT`: Port für Streamlit UI (Standard: 8501)

### 4. Konfigurations-Verzeichnis erstellen

```bash
# Erstelle Config-Verzeichnis
mkdir -p config

# Erstelle initiale Config-Datei (optional)
cat > config/config.yaml << EOF
BATCH_SIZE: 10
BATCH_TIMEOUT: 30
N8N_WEBHOOK_URL: http://100.93.196.41:5678/webhook/discover
WS_RETRY_DELAY: 3
WS_MAX_RETRY_DELAY: 60
N8N_RETRY_DELAY: 5
WS_PING_INTERVAL: 20
WS_PING_TIMEOUT: 10
WS_CONNECTION_TIMEOUT: 30
WS_URI: wss://pumpportal.fun/api/data
BAD_NAMES_PATTERN: test|bot|rug|scam|cant|honey|faucet
HEALTH_PORT: 8000
EOF
```

---

## ⚙️ Konfiguration

### Umgebungsvariablen (.env)

Die `.env` Datei enthält alle konfigurierbaren Werte:

| Variable | Beschreibung | Standard |
|----------|--------------|----------|
| `BATCH_SIZE` | Anzahl Coins pro Batch | 10 |
| `BATCH_TIMEOUT` | Timeout für Batch-Versand (Sekunden) | 30 |
| `N8N_WEBHOOK_URL` | n8n Webhook URL | - |
| `WS_RETRY_DELAY` | WebSocket Retry Delay (Sekunden) | 3 |
| `WS_MAX_RETRY_DELAY` | Maximaler Retry Delay (Sekunden) | 60 |
| `N8N_RETRY_DELAY` | n8n Retry Delay (Sekunden) | 5 |
| `WS_PING_INTERVAL` | WebSocket Ping Interval (Sekunden) | 20 |
| `WS_PING_TIMEOUT` | WebSocket Ping Timeout (Sekunden) | 10 |
| `WS_CONNECTION_TIMEOUT` | WebSocket Connection Timeout (Sekunden) | 30 |
| `WS_URI` | WebSocket URI | wss://pumpportal.fun/api/data |
| `BAD_NAMES_PATTERN` | Regex-Pattern für gefilterte Namen | test\|bot\|rug\|scam\|cant\|honey\|faucet |
| `HEALTH_PORT` | Port für Health/Metrics | 8000 |
| `RELAY_PORT` | Externer Port für Relay | 8000 |
| `UI_PORT` | Port für Streamlit UI | 8501 |

### Konfiguration über Streamlit UI

Die meisten Einstellungen können auch über die Streamlit UI geändert werden (siehe [Streamlit UI](#streamlit-ui)).

---

## 🚀 Start & Betrieb

### 1. Services starten

```bash
# Services im Hintergrund starten
docker compose up -d

# Status prüfen
docker compose ps
```

### 2. Ports prüfen

Nach dem Start sind folgende Ports von außen erreichbar:

| Service | URL | Beschreibung |
|---------|-----|--------------|
| **Streamlit UI** | http://localhost:8501 | Web-Interface für Konfiguration und Monitoring |
| **API Health-Check** | http://localhost:8000/health | Health-Status des Relay-Services |
| **Prometheus Metrics** | http://localhost:8000/metrics | Prometheus-kompatible Metriken |

**Ports anpassen:**
Die Ports können in der `.env` Datei angepasst werden:
```bash
RELAY_PORT=8000    # Port für API & Metrics (Standard: 8000)
UI_PORT=8501       # Port für Streamlit UI (Standard: 8501)
```

Nach Änderungen der Ports:
```bash
docker compose down
docker compose up -d
```

# Logs anzeigen
docker compose logs -f
```

### 2. Services stoppen

```bash
# Services stoppen
docker compose stop

# Services stoppen und Container entfernen
docker compose down

# Services stoppen und Volumes entfernen
docker compose down -v
```

### 3. Services neu starten

```bash
# Services neu starten
docker compose restart

# Einzelnen Service neu starten
docker compose restart relay
docker compose restart ui
```

### 4. Logs anzeigen

```bash
# Alle Logs
docker compose logs -f

# Nur Relay Logs
docker compose logs -f relay

# Nur UI Logs
docker compose logs -f ui

# Letzte 100 Zeilen
docker compose logs --tail=100
```

### 5. Service-Status prüfen

```bash
# Container-Status
docker compose ps

# Health-Check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics
```

---

## 🖥️ Streamlit UI

### Zugriff auf die UI

Nach dem Start ist die Streamlit UI verfügbar unter:
```
http://localhost:8501
```

### Funktionen der UI

#### 1. Dashboard
- **Status-Übersicht**: WebSocket- und n8n-Status
- **Statistiken**: Empfangene Coins, Batches, Uptime
- **Service-Management**: Neustart-Button
- **Auto-Refresh**: Automatische Aktualisierung

#### 2. Konfiguration
- **Batch-Einstellungen**: Batch-Größe, Timeout
- **n8n Einstellungen**: Webhook URL, Retry-Delay
- **WebSocket Einstellungen**: URI, Timeouts, Ping-Intervalle
- **Filter-Einstellungen**: Bad Names Pattern
- **Speichern & Zurücksetzen**: Konfiguration verwalten

**Wichtig:** Nach Änderungen muss der Service neu gestartet werden!

#### 3. Logs
- **Live-Logs**: Echtzeit-Logs vom Relay-Service
- **Konfigurierbare Zeilenanzahl**: 10-1000 Zeilen
- **Auto-Refresh**: Automatische Aktualisierung

#### 4. Metriken
- **Prometheus Metrics**: Vollständige Metriken-Übersicht
- **Wichtige Metriken**: Übersichtliche Darstellung
- **Raw Metrics**: Vollständige Metriken im Text-Format

### Service-Neustart über UI

1. Gehe zu **Dashboard**
2. Klicke auf **"🔄 Service neu starten"**
3. Warte auf Bestätigung
4. Die Seite aktualisiert sich automatisch

---

## 📊 Monitoring & Metriken

### Port-Zugriff

Alle Endpoints sind über die konfigurierten Ports von außen erreichbar:

- **Streamlit UI**: http://localhost:${UI_PORT:-8501}
- **API Health-Check**: http://localhost:${RELAY_PORT:-8000}/health
- **Prometheus Metrics**: http://localhost:${RELAY_PORT:-8000}/metrics

### Health Endpoint

```bash
# Von außerhalb des Containers
curl http://localhost:8000/health

# Oder mit angepasstem Port
curl http://localhost:${RELAY_PORT}/health
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
# Von außerhalb des Containers
curl http://localhost:8000/metrics

# Oder mit angepasstem Port
curl http://localhost:${RELAY_PORT}/metrics
```

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

### Prometheus Integration

Falls du Prometheus verwendest, füge folgende Konfiguration hinzu:

```yaml
scrape_configs:
  - job_name: 'pump-discover'
    static_configs:
      - targets: ['localhost:8000']
```

---

## 🔍 Troubleshooting

### Problem: Service startet nicht

**Lösung:**
```bash
# Prüfe Logs
docker compose logs relay

# Prüfe Container-Status
docker compose ps

# Prüfe Ports
netstat -tulpn | grep -E '8000|8501'
```

### Problem: WebSocket-Verbindung schlägt fehl

**Lösung:**
1. Prüfe Internet-Verbindung
2. Prüfe `WS_URI` in Konfiguration
3. Prüfe Firewall-Einstellungen
4. Prüfe Logs: `docker compose logs -f relay`

### Problem: n8n Webhook nicht erreichbar

**Lösung:**
1. Prüfe `N8N_WEBHOOK_URL` in Konfiguration
2. Teste Webhook manuell:
   ```bash
   curl -X POST http://YOUR_N8N_URL/webhook/discover \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```
3. Prüfe n8n Workflow-Status
4. Prüfe Logs: `docker compose logs -f relay`

### Problem: UI zeigt keine Daten

**Lösung:**
1. Prüfe ob Relay-Service läuft: `docker compose ps`
2. Prüfe Health-Endpoint: `curl http://localhost:8000/health`
3. Prüfe Netzwerk-Verbindung zwischen UI und Relay
4. Prüfe UI-Logs: `docker compose logs -f ui`

### Problem: Konfiguration wird nicht übernommen

**Lösung:**
1. Prüfe ob `.env` Datei korrekt ist
2. Prüfe ob `config/config.yaml` existiert
3. **Wichtig:** Nach Änderungen Service neu starten:
   ```bash
   docker compose restart relay
   ```

### Problem: Docker Socket-Fehler (UI)

**Lösung:**
Die UI benötigt Zugriff auf Docker Socket für Service-Neustart:
```bash
# Prüfe Berechtigungen
ls -la /var/run/docker.sock

# Falls nötig, Berechtigungen anpassen (Vorsicht!)
sudo chmod 666 /var/run/docker.sock
```

**Alternative:** Service-Neustart über Docker Compose:
```bash
docker compose restart relay
```

---

## 📝 Wartung

### Regelmäßige Aufgaben

1. **Logs prüfen**: `docker compose logs --tail=100`
2. **Metriken überwachen**: UI → Metriken
3. **Health-Check**: `curl http://localhost:8000/health`
4. **Updates**: Regelmäßig Docker Images aktualisieren

### Backup

```bash
# Backup Konfiguration
tar -czf config-backup-$(date +%Y%m%d).tar.gz config/

# Backup .env
cp .env .env.backup
```

### Updates

```bash
# Images neu bauen
docker compose build --no-cache

# Services neu starten
docker compose up -d
```

---

## 🔐 Sicherheit

### Empfehlungen:

1. **Firewall**: Nur notwendige Ports öffnen (8000, 8501)
2. **Reverse Proxy**: Nginx/Traefik für UI-Zugriff
3. **HTTPS**: SSL/TLS für UI-Zugriff
4. **Credentials**: `.env` Datei nicht committen
5. **Docker Socket**: Nur für UI-Container, nicht extern exponiert

---

## 📞 Support

Bei Problemen:
1. Prüfe Logs: `docker compose logs -f`
2. Prüfe Health: `curl http://localhost:8000/health`
3. Prüfe Metriken: `curl http://localhost:8000/metrics`
4. Prüfe UI: http://localhost:8501

---

## 📚 Weitere Ressourcen

- **Docker Compose Dokumentation**: https://docs.docker.com/compose/
- **Streamlit Dokumentation**: https://docs.streamlit.io/
- **Prometheus Dokumentation**: https://prometheus.io/docs/

---

**Viel Erfolg mit Pump Discover! 🚀**

