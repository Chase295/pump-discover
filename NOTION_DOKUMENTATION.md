# 🚀 Pump Discover - Gesamtübersicht

> **📝 Hinweis:** Diese Dokumentation kann direkt in Notion importiert werden. Kopiere den Inhalt und füge ihn als Markdown in Notion ein.

---

## ⚙️ KONFIGURATION (Bitte oben anpassen)

### 🔗 URLs & Zugriff

| Service | URL | Status | Beschreibung |
|---------|-----|--------|--------------|
| **Streamlit UI** | `http://localhost:8500` | ✅ | Web-Interface für Konfiguration & Monitoring |
| **API Health-Check** | `http://localhost:8010/health` | ✅ | Health-Status des Relay-Services |
| **Prometheus Metrics** | `http://localhost:8010/metrics` | ✅ | Prometheus-kompatible Metriken |
| **n8n Webhook** | `https://n8n-ai.chase295.de/webhook/pump-discover-beta` | ✅ | n8n Webhook URL |

### 📊 Aktuelle Konfiguration

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| **Relay Port** | `8010` | Externer Port für API & Metrics |
| **UI Port** | `8500` | Externer Port für Streamlit UI |
| **Batch Size** | `10` | Anzahl Coins pro Batch |
| **Batch Timeout** | `30s` | Timeout für Batch-Versand |
| **n8n Webhook Method** | `GET` | HTTP-Methode für n8n (GET/POST) |

### 🗄️ Datenbank

| Parameter | Wert | Beschreibung |
|-----------|------|--------------|
| **Datenbank** | `PostgreSQL` | Datenbank-Typ |
| **Tabelle** | `discovered_coins` | Haupt-Tabelle für Tokens |
| **Schema** | `sql/schema.sql` | SQL-Schema-Datei |

---

## 📋 Projekt-Übersicht

### 🎯 Zweck

Pump Discover ist ein System zur **Echtzeit-Erkennung neuer Pump.fun Tokens** mit automatischer Weiterleitung an n8n für Filterung und Datenbank-Speicherung.

### 🔄 Datenfluss

```
Pump.fun WebSocket
    ↓
Python Relay Service (Filterung, Batching)
    ↓
n8n Webhook (weitere Filterung, Metadata-Extraktion)
    ↓
PostgreSQL Datenbank (discovered_coins Tabelle)
```

### 🏗️ Architektur

Das System besteht aus **3 Hauptkomponenten**:

1. **Python Relay Service** (`relay/`)
   - Empfängt Tokens über WebSocket von Pump.fun
   - Führt erste Filterung durch (Bad Names, Spam-Burst)
   - Sendet Batches an n8n
   - Bietet Health-Check und Prometheus Metrics

2. **Streamlit UI** (`ui/`)
   - Web-Interface für Konfiguration
   - Live-Monitoring (Dashboard, Logs, Metriken)
   - Service-Management (Neustart, Konfiguration)

3. **n8n Workflow** (extern)
   - Empfängt Batches vom Relay
   - Extrahiert Metadata (IPFS/RapidLaunch)
   - Führt weitere Filterung durch
   - Speichert Daten in PostgreSQL

---

## 🚀 Schnellstart

### 1. Services starten

```bash
cd /path/to/pump-discover
docker compose up -d
```

### 2. Status prüfen

```bash
# Container-Status
docker compose ps

# Logs anzeigen
docker compose logs -f

# Health-Check
curl http://localhost:8010/health
```

### 3. UI öffnen

Öffne im Browser: **http://localhost:8500**

---

## 📡 API Endpoints

### Health Check

**Endpoint:** `GET /health`

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

**Status-Codes:**
- `200` - Service ist gesund (WebSocket verbunden)
- `503` - Service ist degradiert (WebSocket nicht verbunden)

### Prometheus Metrics

**Endpoint:** `GET /metrics`

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

---

## ⚙️ Konfiguration

### Umgebungsvariablen (.env)

Die Konfiguration erfolgt über die `.env` Datei oder über die Streamlit UI.

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `BATCH_SIZE` | `10` | Anzahl Coins pro Batch |
| `BATCH_TIMEOUT` | `30` | Timeout für Batch-Versand (Sekunden) |
| `N8N_WEBHOOK_URL` | - | n8n Webhook URL (leer = nicht konfiguriert) |
| `N8N_WEBHOOK_METHOD` | `POST` | HTTP-Methode (POST/GET) |
| `WS_URI` | `wss://pumpportal.fun/api/data` | WebSocket URI |
| `WS_RETRY_DELAY` | `3` | WebSocket Retry Delay (Sekunden) |
| `WS_MAX_RETRY_DELAY` | `60` | Maximaler Retry Delay (Sekunden) |
| `WS_PING_INTERVAL` | `20` | WebSocket Ping Interval (Sekunden) |
| `WS_PING_TIMEOUT` | `10` | WebSocket Ping Timeout (Sekunden) |
| `WS_CONNECTION_TIMEOUT` | `30` | WebSocket Connection Timeout (Sekunden) |
| `N8N_RETRY_DELAY` | `5` | n8n Retry Delay (Sekunden) |
| `BAD_NAMES_PATTERN` | `test\|bot\|rug\|scam\|cant\|honey\|faucet` | Regex-Pattern für gefilterte Namen |
| `HEALTH_PORT` | `8000` | Port für Health/Metrics (intern) |
| `RELAY_PORT` | `8010` | Externer Port für Relay |
| `UI_PORT` | `8500` | Externer Port für UI |

### Konfiguration über UI

Die meisten Einstellungen können über die Streamlit UI geändert werden:

1. Öffne **http://localhost:8500**
2. Gehe zu **"⚙️ Konfiguration"** Tab
3. Ändere die Werte
4. Klicke auf **"💾 Konfiguration speichern"**
5. Starte den Service neu über **"🔄 Relay-Service neu starten"**

---

## 🗄️ Datenbankschema

### Tabelle: `discovered_coins`

Haupt-Tabelle für alle entdeckten Pump.fun Tokens.

**Wichtige Felder:**

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `token_address` | VARCHAR(64) | Mint-Adresse (PRIMARY KEY) |
| `name` | VARCHAR(255) | Token-Name |
| `symbol` | VARCHAR(30) | Token-Symbol |
| `signature` | VARCHAR(88) | Transaktions-Signatur |
| `trader_public_key` | VARCHAR(44) | Creator-Public-Key |
| `bonding_curve_key` | VARCHAR(44) | Bonding Curve Adresse |
| `pool_address` | VARCHAR(64) | Pool-Adresse |
| `market_cap_sol` | NUMERIC(20, 2) | Market Cap in SOL |
| `liquidity_sol` | NUMERIC(20, 6) | Liquidität in SOL |
| `price_sol` | NUMERIC(30, 18) | Preis in SOL |
| `open_market_cap_sol` | NUMERIC(20, 2) | Open Market Cap (85000) |
| `metadata_uri` | TEXT | URI zur Metadata |
| `discovered_at` | TIMESTAMP | Wann wurde der Coin entdeckt |
| `is_graduated` | BOOLEAN | Ob der Token graduiert ist |
| `is_active` | BOOLEAN | Ob der Token noch aktiv ist |

**Vollständiges Schema:** Siehe `sql/schema.sql`

### SQL Views

Für berechnete Metriken und USD-Konvertierungen:

- `discovered_coins_graduation` - Graduierungs-Metriken
- `discovered_coins_active` - Aktive Coins mit Metriken
- `discovered_coins_near_graduation` - Coins kurz vor Graduierung
- `discovered_coins_with_usd` - Coins mit USD-Werten (benötigt `exchange_rates` Tabelle)

**Vollständige Views:** Siehe `sql/views.sql`

---

## 📊 Daten-Mapping

### WebSocket → SQL

Die folgenden Felder werden direkt vom WebSocket übernommen:

| WebSocket Feld | SQL Feld | Status |
|----------------|----------|--------|
| `mint` | `token_address` | ✅ Direkt |
| `name` | `name` | ✅ Direkt |
| `symbol` | `symbol` | ✅ Direkt |
| `signature` | `signature` | ✅ Direkt |
| `traderPublicKey` | `trader_public_key` | ✅ Direkt |
| `bondingCurveKey` | `bonding_curve_key` | ✅ Direkt |
| `bondingCurveKey` | `pool_address` | ✅ Direkt |
| `vTokensInBondingCurve` | `v_tokens_in_bonding_curve` | ✅ Direkt |
| `vSolInBondingCurve` | `v_sol_in_bonding_curve` | ✅ Direkt |
| `vSolInBondingCurve` | `liquidity_sol` | ✅ Direkt |
| `initialBuy` | `initial_buy_tokens` | ✅ Direkt |
| `solAmount` | `initial_buy_sol` | ✅ Direkt |
| `marketCapSol` | `market_cap_sol` | ✅ Direkt |
| `marketCapSol / vTokensInBondingCurve` | `price_sol` | ✅ Berechnet |
| `is_mayhem_mode` | `is_mayhem_mode` | ✅ Direkt |
| `pool` | `pool_type` | ✅ Direkt |
| `uri` | `metadata_uri` | ✅ Direkt |

### Metadata-Extraktion (n8n)

Die folgenden Felder werden aus der Metadata URI extrahiert:

| Metadata Feld | SQL Feld | Status |
|---------------|----------|--------|
| `metadata.description` | `description` | ⚠️ Aus Metadata |
| `metadata.image` | `image_url` | ⚠️ Aus Metadata |
| `metadata.twitter` | `twitter_url` | ⚠️ Aus Metadata |
| `metadata.telegram` | `telegram_url` | ⚠️ Aus Metadata |
| `metadata.website` | `website_url` | ⚠️ Aus Metadata |
| `metadata.discord` | `discord_url` | ⚠️ Aus Metadata |

**Vollständiges Mapping:** Siehe `DATEN_MAPPING.md`

---

## 🔧 Service-Management

### Container-Verwaltung

```bash
# Services starten
docker compose up -d

# Services stoppen
docker compose stop

# Services neu starten
docker compose restart

# Services stoppen und entfernen
docker compose down

# Logs anzeigen
docker compose logs -f

# Logs eines bestimmten Services
docker compose logs -f relay
docker compose logs -f ui
```

### Service-Neustart über UI

1. Öffne **http://localhost:8500**
2. Gehe zu **"📊 Dashboard"** Tab
3. Klicke auf **"🔄 Service neu starten"**

### Konfiguration ändern

1. Öffne **http://localhost:8500**
2. Gehe zu **"⚙️ Konfiguration"** Tab
3. Ändere die Werte
4. Klicke auf **"💾 Konfiguration speichern"**
5. Starte den Service neu

---

## 📈 Monitoring & Metriken

### Streamlit UI Dashboard

Das Dashboard zeigt:

- **Status-Übersicht**: WebSocket-Status, n8n-Status, Uptime
- **Coin-Statistiken**: Gesamt empfangene Coins, Batches gesendet
- **Detaillierte Informationen**: Reconnects, letzte Nachricht, Fehler
- **Service-Management**: Neustart-Button, Auto-Refresh

### Prometheus Integration

Die Metriken können von Prometheus abgerufen werden:

```yaml
scrape_configs:
  - job_name: 'pump-discover'
    static_configs:
      - targets: ['localhost:8010']
```

### Wichtige Metriken

- **`pumpfun_coins_received_total`** - Gesamt empfangene Coins
- **`pumpfun_coins_sent_total`** - Gesamt gesendete Coins
- **`pumpfun_coins_filtered_total`** - Gefilterte Coins (nach Grund)
- **`pumpfun_batches_sent_total`** - Gesamt gesendete Batches
- **`pumpfun_ws_reconnects_total`** - WebSocket Reconnects
- **`pumpfun_ws_connected`** - WebSocket Verbindungsstatus (1=connected)
- **`pumpfun_n8n_available`** - n8n Verfügbarkeit (1=available)
- **`pumpfun_buffer_size`** - Aktuelle Buffer-Größe
- **`pumpfun_uptime_seconds`** - Uptime in Sekunden

---

## 🐛 Troubleshooting

### Problem: Service startet nicht

**Lösung:**
```bash
# Prüfe Logs
docker compose logs relay

# Prüfe Container-Status
docker compose ps

# Prüfe Ports
netstat -tulpn | grep -E '8010|8500'
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
   curl -X GET "https://n8n-ai.chase295.de/webhook/pump-discover-beta?data=test"
   ```
3. Prüfe n8n Workflow-Status
4. Prüfe Logs: `docker compose logs -f relay`

### Problem: UI zeigt keine Daten

**Lösung:**
1. Prüfe ob Relay-Service läuft: `docker compose ps`
2. Prüfe Health-Check: `curl http://localhost:8010/health`
3. Prüfe Logs: `docker compose logs -f ui`
4. Prüfe ob Ports korrekt sind

### Problem: Coins werden nicht empfangen

**Lösung:**
1. Prüfe WebSocket-Status im Dashboard
2. Prüfe Logs: `docker compose logs -f relay`
3. Prüfe ob WebSocket URI korrekt ist
4. Prüfe ob Filter zu restriktiv sind

---

## 📚 Weitere Dokumentation

### Projekt-Dateien

- **README.md** - Haupt-README mit Schnellstart
- **ANLEITUNG.md** - Vollständige Setup-Anleitung
- **DATEN_MAPPING.md** - WebSocket → SQL Mapping (für n8n)
- **PROJEKT_STRUKTUR.md** - Detaillierte Projektstruktur
- **api/swagger.yaml** - OpenAPI/Swagger Spezifikation

### Code-Dokumentation

- **relay/main.py** - Python Relay Service
- **ui/app.py** - Streamlit UI
- **sql/schema.sql** - Datenbankschema
- **sql/views.sql** - SQL Views

### Zusätzliche Dokumentation

- **docs/websocket_schema_vergleich.md** - WebSocket vs. SQL Schema Vergleich
- **docs/SCHEMA_UEBERSICHT.md** - Detaillierte Schema-Übersicht

---

## 🔐 Sicherheit & Best Practices

### Umgebungsvariablen

- **Niemals** `.env` Dateien in Git committen
- Verwende starke Passwörter für Datenbank-Zugänge
- Prüfe n8n Webhook URLs auf Gültigkeit

### Netzwerk

- Ports sollten nur lokal erreichbar sein (oder über Firewall geschützt)
- Verwende HTTPS für n8n Webhooks (wenn möglich)
- Prüfe Firewall-Regeln regelmäßig

### Monitoring

- Überwache Logs regelmäßig
- Setze Alerts für kritische Metriken
- Prüfe Health-Check regelmäßig

---

## 📝 Changelog & Updates

### Aktuelle Version

- **Relay Service**: v1.0.0
- **UI**: v1.0.0
- **Docker Compose**: v2.0+

### Features

- ✅ WebSocket-Relay für Pump.fun Tokens
- ✅ n8n-Integration für Filterung
- ✅ Streamlit UI für Management
- ✅ Prometheus Metrics
- ✅ Health-Checks
- ✅ Konfigurierbare Filter
- ✅ Service-Neustart über UI
- ✅ Live-Logs und Metriken
- ✅ Input-Validierung
- ✅ Auto-Erstellung von .env Datei
- ✅ price_sol Berechnung
- ✅ pool_address Mapping

---

## 📞 Support & Kontakt

Bei Fragen oder Problemen:

1. Prüfe die **Troubleshooting** Sektion
2. Prüfe die **Logs**: `docker compose logs -f`
3. Prüfe die **Health-Check**: `curl http://localhost:8010/health`
4. Prüfe die **Dokumentation** in den Projekt-Dateien

---

## 📄 Lizenz

Siehe LICENSE Datei (falls vorhanden).

---

**Letzte Aktualisierung:** 2024-12-25  
**Version:** 1.0.0  
**Status:** ✅ Produktiv

