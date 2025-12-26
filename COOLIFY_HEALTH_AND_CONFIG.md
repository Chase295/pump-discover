# 🔧 Coolify Health-Status & Dynamische Konfiguration - Technische Dokumentation

## 📋 Übersicht

Diese Dokumentation erklärt im Detail, wie zwei kritische Features implementiert wurden:

1. **Health-Status in Coolify korrekt anzeigen** - Warum Container nicht mehr "running unknown" zeigen
2. **Dynamische Konfiguration über UI** - Wie Änderungen ohne vollständigen Neustart übernommen werden

---

## 1️⃣ Health-Status in Coolify korrekt anzeigen

### 🎯 Problem

In Coolify wurden Container als **"running unknown"** angezeigt, obwohl sie liefen. Coolify konnte den Health-Status nicht erkennen.

### ✅ Lösung: Healthcheck-Implementierung

Die Lösung besteht aus **3 Komponenten**:

#### **A) Health-Check Endpoint im Relay-Service**

**Datei:** `relay/main.py`

```python
async def health_check(request):
    """Health Check Endpoint mit detaillierten Infos"""
    ws_status = relay_status.get("ws_connected", False)
    n8n_status = relay_status.get("n8n_available", False)  # Default: False
    uptime = time.time() - relay_status["start_time"]
    last_coin = relay_status.get("last_coin_time")
    last_msg = relay_status.get("last_message_time")
    
    health_data = {
        "status": "healthy" if ws_status else "degraded",
        "ws_connected": ws_status,
        "n8n_available": n8n_status,
        "n8n_webhook_url": N8N_WEBHOOK_URL if N8N_WEBHOOK_URL else "NICHT GESETZT",
        "uptime_seconds": int(uptime),
        "total_coins": relay_status["total_coins"],
        "total_batches": relay_status["total_batches"],
        "last_coin_ago": int(time.time() - last_coin) if last_coin else None,
        "last_message_ago": int(time.time() - last_msg) if last_msg else None,
        "reconnect_count": relay_status["reconnect_count"],
        "last_error": relay_status.get("last_error")
    }
    
    status_code = 200 if ws_status else 503
    return web.json_response(health_data, status=status_code)
```

**Wichtig:**
- Endpoint gibt **HTTP 200** zurück, wenn WebSocket verbunden ist
- Endpoint gibt **HTTP 503** zurück, wenn WebSocket nicht verbunden ist
- Coolify interpretiert HTTP 200 als "healthy", HTTP 503 als "unhealthy"

**Endpoint-Registrierung:**
```python
async def start_health_server():
    """Startet Health + Metrics Server"""
    app = web.Application()
    app.add_routes([
        web.get("/health", health_check),  # ← Health-Check Endpoint
        web.get("/metrics", metrics_handler),
        web.get("/logs", logs_handler),
        web.post("/reload-config", reload_config_handler)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HEALTH_PORT)
    await site.start()
```

#### **B) Healthcheck im Dockerfile**

**Datei:** `relay/Dockerfile`

```dockerfile
# Installation von curl (für Healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Healthcheck
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**Erklärung:**
- `--interval=10s`: Healthcheck alle 10 Sekunden
- `--timeout=5s`: Timeout nach 5 Sekunden
- `--start-period=10s`: 10 Sekunden Startzeit (Container braucht Zeit zum Starten)
- `--retries=5`: 5 Versuche, bevor Container als "unhealthy" markiert wird
- `curl -f`: Gibt Exit-Code 1 zurück, wenn HTTP-Status nicht 200 ist

#### **C) Healthcheck in docker-compose.yaml**

**Datei:** `docker-compose.yaml`

```yaml
api:
  # ... andere Konfiguration ...
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 10s
```

**Warum beide?**
- **Dockerfile Healthcheck**: Funktioniert auch ohne docker-compose (z.B. bei `docker run`)
- **docker-compose Healthcheck**: Überschreibt Dockerfile-Healthcheck und ist für Coolify wichtig

**Coolify verwendet docker-compose Healthchecks**, daher ist dieser entscheidend!

#### **D) Healthcheck für UI-Service**

**Datei:** `ui/Dockerfile`

```dockerfile
# Installation von curl (für Healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Healthcheck für Streamlit
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1
```

**Streamlit hat einen eingebauten Health-Endpoint:** `/_stcore/health`

**In docker-compose.yaml:**
```yaml
web:
  # ... andere Konfiguration ...
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 20s
```

### 🔄 Funktionsweise

1. **Container startet** → Coolify wartet `start_period` (10s für API, 20s für UI)
2. **Healthcheck läuft** → Alle `interval` Sekunden wird `/health` aufgerufen
3. **Status-Prüfung**:
   - HTTP 200 → Container ist "healthy" ✅
   - HTTP 503 oder Timeout → Container ist "unhealthy" ❌
4. **Coolify zeigt Status** → "healthy" / "unhealthy" statt "running unknown"

### 📊 Ergebnis

- ✅ Container zeigen korrekten Health-Status in Coolify
- ✅ "running unknown" Problem ist gelöst
- ✅ Coolify kann automatisch erkennen, wenn Container nicht mehr funktioniert

---

## 2️⃣ Dynamische Konfiguration über UI

### 🎯 Problem

**Vorher:**
- Konfiguration wurde in `.env` gespeichert
- Service musste **komplett neu gestartet** werden, damit Änderungen wirksam wurden
- In Coolify: Neustart = Neues Deployment = Alle Einstellungen gehen verloren

**Anforderungen:**
- Konfiguration über UI ändern
- Änderungen **ohne vollständigen Neustart** übernehmen
- Funktioniert auch in Coolify (ohne Docker Socket)

### ✅ Lösung: Dynamisches Config-Reloading

Die Lösung besteht aus **4 Komponenten**:

#### **A) Geteiltes Volume für Konfiguration**

**Datei:** `docker-compose.yaml`

```yaml
services:
  api:
    volumes:
      - config_data:/app/config:rw  # ← Named Volume
  
  web:
    volumes:
      - config_data:/app/config:rw  # ← Gleiches Volume (geteilt)

volumes:
  config_data:  # ← Named Volume (persistent in Coolify)
```

**Warum Named Volume?**
- **Coolify-kompatibel**: Named Volumes werden in Coolify persistent gespeichert
- **Geteilt**: Beide Services (API + UI) können auf dieselbe Datei zugreifen
- **Persistent**: Überlebt Container-Neustarts

**Pfad:** `/app/config/.env` (innerhalb des Volumes)

#### **B) Config-Loading im Relay-Service**

**Datei:** `relay/main.py`

```python
CONFIG_VOLUME_PATH = "/app/config/.env"

def load_config():
    """Lädt Konfiguration aus Environment Variables und Config-Datei (Volume)"""
    global BATCH_SIZE, BATCH_TIMEOUT, N8N_WEBHOOK_URL, N8N_WEBHOOK_METHOD
    # ... alle anderen Variablen ...
    
    # 1. Lade aus Environment Variables (Coolify)
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()
    # ... alle anderen ...
    
    # 2. Überschreibe mit Config-Datei aus Volume (wenn vorhanden)
    config_file = "/app/config/.env"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        # Überschreibe globale Variablen
                        if key == "BATCH_SIZE" and value.isdigit():
                            BATCH_SIZE = int(value)
                        elif key == "N8N_WEBHOOK_URL":
                            N8N_WEBHOOK_URL = value
                        # ... alle anderen Felder ...
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Config-Datei: {e}", flush=True)
```

**Wichtig:**
- Config wird **beim Start** geladen (`load_config()` in `main()`)
- Config wird **auch zur Laufzeit** neu geladen (siehe `/reload-config` Endpoint)

#### **C) Reload-Endpoint im Relay-Service**

**Datei:** `relay/main.py`

```python
async def reload_config_handler(request):
    """Lädt die Konfiguration neu (ohne Neustart)"""
    try:
        load_config()  # ← Lädt Config-Datei erneut
        add_log("🔄 Konfiguration wurde neu geladen!")
        return web.json_response({
            "status": "success",
            "message": "Konfiguration wurde neu geladen",
            "n8n_webhook_url": N8N_WEBHOOK_URL if N8N_WEBHOOK_URL else "NICHT GESETZT"
        })
    except Exception as e:
        add_log(f"❌ Fehler beim Neuladen der Konfiguration: {e}")
        return web.json_response({
            "status": "error",
            "message": str(e)
        }, status=500)
```

**Registrierung:**
```python
app.add_routes([
    web.get("/health", health_check),
    web.get("/metrics", metrics_handler),
    web.get("/logs", logs_handler),
    web.post("/reload-config", reload_config_handler)  # ← Reload-Endpoint
])
```

**Funktionsweise:**
1. UI sendet POST-Request an `/reload-config`
2. Relay-Service liest `/app/config/.env` erneut
3. Globale Variablen werden aktualisiert
4. Neue Konfiguration ist sofort aktiv (ohne Neustart!)

#### **D) UI: Config speichern und neu laden**

**Datei:** `ui/app.py`

**1. Config speichern:**
```python
def save_config(config):
    """Speichert Konfiguration in YAML-Datei UND .env Datei"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    # Speichere YAML (für UI)
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    # Speichere .env (für Relay Service) ← WICHTIG!
    env_file = "/app/config/.env"  # ← Im geteilten Volume
    env_content = f"""# Batch-Einstellungen
BATCH_SIZE={config.get('BATCH_SIZE', 10)}
BATCH_TIMEOUT={config.get('BATCH_TIMEOUT', 30)}

# n8n Webhook
N8N_WEBHOOK_URL={config.get('N8N_WEBHOOK_URL', '')}
N8N_WEBHOOK_METHOD={config.get('N8N_WEBHOOK_METHOD', 'POST')}

# ... alle anderen Felder ...
"""
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    return True
```

**2. Config neu laden (ohne Neustart):**
```python
def reload_config():
    """Lädt die Konfiguration im Relay-Service neu (ohne Neustart)"""
    try:
        # POST-Request an Relay-Service
        response = requests.post(
            f"http://{RELAY_SERVICE}:{RELAY_PORT}/reload-config",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            return True, data.get("message", "Konfiguration wurde neu geladen")
        else:
            return False, f"Fehler: HTTP {response.status_code}"
    except Exception as e:
        return False, f"Fehler beim Neuladen: {str(e)}"
```

**3. UI-Button:**
```python
# In der UI (Konfigurations-Tab)
if st.button("🔄 Konfiguration neu laden", type="primary"):
    with st.spinner("Konfiguration wird neu geladen..."):
        success, message = reload_config()
        if success:
            st.success(message)
            st.info("💡 Die neue Konfiguration ist jetzt aktiv! Kein Neustart nötig.")
        else:
            st.error(message)
```

### 🔄 Kompletter Datenfluss

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER ändert Konfiguration in UI                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. UI speichert in /app/config/.env (geteiltes Volume)     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. USER klickt "Konfiguration neu laden"                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. UI sendet POST http://api:8000/reload-config            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Relay-Service liest /app/config/.env erneut             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Globale Variablen werden aktualisiert                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Neue Konfiguration ist SOFORT aktiv! ✅                  │
└─────────────────────────────────────────────────────────────┘
```

### 📊 Vorteile

**✅ Kein vollständiger Neustart nötig:**
- WebSocket-Verbindung bleibt bestehen
- Keine Downtime
- Änderungen sind sofort aktiv

**✅ Funktioniert in Coolify:**
- Kein Docker Socket nötig
- Kein `docker compose restart` nötig
- Alles über HTTP-API

**✅ Persistenz:**
- Config wird in Named Volume gespeichert
- Überlebt Container-Neustarts
- Coolify speichert Named Volumes persistent

### ⚠️ Wichtige Hinweise

**Was wird dynamisch neu geladen?**
- ✅ `BATCH_SIZE`, `BATCH_TIMEOUT`
- ✅ `N8N_WEBHOOK_URL`, `N8N_WEBHOOK_METHOD`
- ✅ `WS_URI`, `WS_RETRY_DELAY`, etc.
- ✅ `BAD_NAMES_PATTERN`
- ✅ Alle anderen Config-Werte

**Was wird NICHT dynamisch neu geladen?**
- ❌ `HEALTH_PORT` (Port kann nicht zur Laufzeit geändert werden)
- ❌ Environment Variables aus Coolify (müssen über Coolify-UI geändert werden)

**Fallback:**
- Falls `/reload-config` nicht funktioniert, kann in Coolify der `api` Service manuell neu gestartet werden
- Config bleibt im Volume erhalten und wird beim Neustart geladen

---

## 🔧 Technische Details

### Service-Kommunikation

**In Coolify:**
- Services kommunizieren über **Service-Namen** im Docker-Netzwerk
- UI → API: `http://api:8000/reload-config`
- `RELAY_SERVICE=api` (Environment Variable in UI-Container)

**Lokal:**
- Services kommunizieren über **Container-Namen** oder **Service-Namen**
- UI → API: `http://pump-discover-relay:8000/reload-config` oder `http://api:8000/reload-config`

### Volume-Mounting

**Pfad im Container:**
- `/app/config/.env` (für beide Services)

**Pfad auf Host (lokal):**
- Wird von Docker verwaltet (Named Volume)

**Pfad in Coolify:**
- Wird von Coolify verwaltet (persistent gespeichert)

### Fehlerbehandlung

**Wenn Config-Datei nicht existiert:**
- Relay verwendet Environment Variables (Fallback)
- UI erstellt Default-Config beim ersten Start

**Wenn Reload fehlschlägt:**
- UI zeigt Fehlermeldung
- User kann Service manuell neu starten (in Coolify über Dashboard)

---

## 📝 Zusammenfassung

### Health-Status

1. **Health-Check Endpoint** (`/health`) gibt HTTP 200/503 zurück
2. **Dockerfile Healthcheck** prüft Endpoint alle 10s
3. **docker-compose Healthcheck** überschreibt Dockerfile-Healthcheck
4. **Coolify** interpretiert Healthcheck-Status und zeigt "healthy"/"unhealthy"

### Dynamische Konfiguration

1. **Geteiltes Volume** (`config_data`) für beide Services
2. **UI speichert** Config in `/app/config/.env`
3. **Relay lädt** Config beim Start und zur Laufzeit
4. **Reload-Endpoint** (`/reload-config`) lädt Config ohne Neustart
5. **UI ruft** Reload-Endpoint auf, wenn User "Konfiguration neu laden" klickt

**Ergebnis:** 
- ✅ Health-Status wird korrekt in Coolify angezeigt
- ✅ Konfiguration kann ohne Neustart geändert werden
- ✅ Funktioniert perfekt in Coolify (ohne Docker Socket)

---

## 🚀 Deployment-Checkliste

- [ ] Healthcheck in `docker-compose.yaml` für beide Services
- [ ] `curl` in beiden Dockerfiles installiert
- [ ] Named Volume `config_data` in `docker-compose.yaml` definiert
- [ ] Beide Services mounten `/app/config:rw`
- [ ] `/reload-config` Endpoint im Relay-Service registriert
- [ ] UI speichert Config in `/app/config/.env`
- [ ] UI ruft `/reload-config` auf, wenn User "neu laden" klickt

---

**Erstellt:** 2025-12-26  
**Version:** 1.0  
**Autor:** Pump Discover Team

