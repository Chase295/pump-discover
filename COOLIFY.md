# 🚀 Coolify Deployment Anleitung

## 📋 Übersicht

Diese Anleitung erklärt, wie du Pump Discover auf Coolify deployst.

**Ports:**
- **Web (UI)**: Port `8500`
- **API (Relay)**: Port `8010`

---

## 🔧 Coolify Setup

### Option 1: Mit `dockercompose.yaml` (Empfohlen)

1. **Repository in Coolify verbinden:**
   - Gehe zu deinem Coolify Dashboard
   - Klicke auf "New Resource" → "Docker Compose"
   - Verbinde dein GitHub Repository: `https://github.com/Chase295/pump-discover`

2. **docker-compose.yml auswählen:**
   - Coolify erkennt automatisch `docker-compose.yml` (Standard-Name)
   - Falls nicht automatisch erkannt, wähle manuell `docker-compose.yml` als Compose-Datei
   - Coolify erkennt automatisch die Services `web` und `api`

3. **Ports konfigurieren:**
   - **Web Service**: Port `8500` (wird automatisch erkannt)
   - **API Service**: Port `8010` (wird automatisch erkannt)

4. **Environment Variables setzen:**
   - Füge in Coolify die folgenden Environment Variables hinzu:
     ```
     BATCH_SIZE=10
     BATCH_TIMEOUT=30
     N8N_WEBHOOK_URL=https://deine-n8n-url/webhook/discover
     N8N_WEBHOOK_METHOD=POST
     WS_URI=wss://pumpportal.fun/api/data
     BAD_NAMES_PATTERN=test|bot|rug|scam|cant|honey|faucet
     ```

5. **Deploy:**
   - Klicke auf "Deploy"
   - Coolify baut die Container und startet die Services

---

## 🌐 Domain & Reverse Proxy

Coolify kann automatisch einen Reverse Proxy (Traefik) konfigurieren:

### Web UI (Port 8500)
- **Domain**: z.B. `pump-discover.yourdomain.com`
- **Port**: `8500`
- **Path**: `/` (Root)

### API (Port 8010)
- **Domain**: z.B. `api.pump-discover.yourdomain.com`
- **Port**: `8010`
- **Endpoints**:
  - `/health` - Health Check
  - `/metrics` - Prometheus Metrics

---

## 🔍 Service-Erkennung

### Interne Service-Kommunikation

In Coolify kommunizieren die Services über das interne Netzwerk:

- **UI → Relay**: 
  - Service-Name: `api` (aus `dockercompose.yaml`)
  - Port: `8000` (intern)
  - URL: `http://api:8000/health`

Die UI erkennt automatisch den Relay-Service über die Environment Variable:
```yaml
RELAY_SERVICE=api  # Service-Name aus dockercompose.yaml
RELAY_PORT=8000    # Interner Port
COOLIFY_MODE=true  # Aktiviert Coolify-Modus (deaktiviert Docker Socket Features)
```

### Wichtiger Hinweis: Docker Socket

**In Coolify ist kein Docker Socket verfügbar!** Daher:
- ❌ Service-Neustart über UI funktioniert nicht → Muss über Coolify-Dashboard erfolgen
- ❌ Logs-Anzeige über UI funktioniert nicht → Muss über Coolify-Dashboard erfolgen
- ✅ Health-Check und Metrics funktionieren weiterhin über HTTP-API
- ✅ Konfiguration speichern funktioniert (wird in Volume gespeichert)

---

## 📊 Health Checks

### Web UI
- **URL**: `http://your-domain:8500`
- **Status**: Sollte automatisch laden

### API
- **Health Check**: `http://your-domain:8010/health`
- **Metrics**: `http://your-domain:8010/metrics`

**Test:**
```bash
curl http://your-domain:8010/health
```

---

## 🔐 Environment Variables

### Wichtige Variablen für Coolify:

| Variable | Beschreibung | Standard | Erforderlich |
|----------|--------------|----------|--------------|
| `BATCH_SIZE` | Anzahl Coins pro Batch | `10` | Nein |
| `BATCH_TIMEOUT` | Batch Timeout (Sekunden) | `30` | Nein |
| `N8N_WEBHOOK_URL` | n8n Webhook URL | - | **Ja** |
| `N8N_WEBHOOK_METHOD` | HTTP Methode (GET/POST) | `POST` | Nein |
| `WS_URI` | WebSocket URI | `wss://pumpportal.fun/api/data` | Nein |
| `BAD_NAMES_PATTERN` | Filter-Pattern | `test\|bot\|rug\|scam` | Nein |

### In Coolify setzen:

1. Gehe zu deinem Service
2. Klicke auf "Environment Variables"
3. Füge die Variablen hinzu
4. Klicke auf "Save & Deploy"

---

## 🐛 Troubleshooting

### Problem: UI kann Relay nicht erreichen

**Lösung:**
- Prüfe, ob beide Services im gleichen Netzwerk sind (`pump-discover-network`)
- Prüfe, ob `RELAY_SERVICE=api` in der UI-Environment gesetzt ist
- Prüfe die Logs im Coolify-Dashboard (Service 'web')

### Problem: Service-Neustart funktioniert nicht in UI

**Lösung:**
- Das ist normal in Coolify! Der Docker Socket ist nicht verfügbar.
- Starte den Service über das Coolify-Dashboard:
  1. Gehe zu deinem Coolify-Dashboard
  2. Wähle den 'api' Service
  3. Klicke auf "Restart"

### Problem: Logs werden nicht angezeigt

**Lösung:**
- Das ist normal in Coolify! Der Docker Socket ist nicht verfügbar.
- Zeige Logs über das Coolify-Dashboard:
  1. Gehe zu deinem Coolify-Dashboard
  2. Wähle den entsprechenden Service ('web' oder 'api')
  3. Klicke auf "Logs"

### Problem: Ports nicht erreichbar

**Lösung:**
- Prüfe, ob Coolify die Ports korrekt gemappt hat
- Prüfe Firewall-Regeln
- Prüfe, ob die Services laufen: `docker ps`

### Problem: WebSocket-Verbindung fehlgeschlagen

**Lösung:**
- Prüfe, ob `WS_URI` korrekt gesetzt ist
- Prüfe Firewall für WebSocket-Verbindungen (Port 443 für wss://)
- Prüfe die Relay-Logs: `docker logs pump-discover-relay`

---

## 📚 Weitere Informationen

- **Projekt-Dokumentation**: Siehe [README.md](README.md)
- **Setup-Anleitung**: Siehe [ANLEITUNG.md](ANLEITUNG.md)
- **API-Dokumentation**: Siehe [api/swagger.yaml](api/swagger.yaml)

---

## ✅ Checkliste für Coolify Deployment

- [ ] Repository in Coolify verbunden
- [ ] `coolify.yml` oder `docker-compose.yml` ausgewählt
- [ ] Ports konfiguriert (8500 für Web, 8010 für API)
- [ ] Environment Variables gesetzt (besonders `N8N_WEBHOOK_URL`)
- [ ] Services deployed
- [ ] Health Checks erfolgreich
- [ ] Web UI erreichbar
- [ ] API erreichbar (`/health` und `/metrics`)

---

**Viel Erfolg mit deinem Deployment! 🚀**

