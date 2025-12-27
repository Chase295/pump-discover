# 📊 Grafana Dashboard für Pump Discover

## 🚀 Schnellstart

### 1. Dashboard importieren

1. Öffne Grafana → **Dashboards** → **Import**
2. Klicke auf **Upload JSON file**
3. Wähle die Datei `pump-discover-dashboard.json`
4. Wähle deinen **Prometheus Datasource** aus
5. Klicke auf **Import**

### 2. Prometheus Datasource konfigurieren

**Falls noch nicht konfiguriert:**

1. Grafana → **Configuration** → **Data Sources**
2. Klicke auf **Add data source**
3. Wähle **Prometheus**
4. **URL:** `http://localhost:8010` (oder deine API-URL)
5. Klicke auf **Save & Test**

**Wichtig:** Der Metrics-Endpoint ist unter `/metrics` erreichbar:
- Lokal: `http://localhost:8010/metrics`
- Coolify: `http://your-domain:8010/metrics`

## 📈 Dashboard-Übersicht

Das Dashboard enthält **19 Panels** in folgenden Kategorien:

### 🔴 Status & Verfügbarkeit
- **WebSocket Status** - Online/Offline Indikator
- **n8n Status** - Verfügbarkeit des n8n Webhooks

### 📊 Coin-Verarbeitung
- **Coin-Verarbeitungsrate** - Coins empfangen/gesendet pro Sekunde
- **Coins empfangen (Total)** - Gesamtanzahl empfangener Coins
- **Coins gesendet (Total)** - Gesamtanzahl gesendeter Coins
- **Batches gesendet (Total)** - Gesamtanzahl gesendeter Batches
- **Gefilterte Coins** - Aufgeschlüsselt nach Grund (Spam Burst, Bad Name)

### ⚡ Performance
- **Batch-Versandrate** - Batches pro Sekunde
- **Batch-Versand Dauer (Latency)** - p50, p95, p99, Durchschnitt
- **Buffer Größe** - Aktuelle Buffer-Größe (Gauge)
- **WebSocket Reconnects** - Anzahl der Reconnects

### 💻 System-Ressourcen
- **Memory Usage** - Resident & Virtual Memory
- **CPU Usage** - CPU-Auslastung in Prozent
- **Python GC Collections** - Garbage Collection Rate
- **File Descriptors** - Offene & Max File Descriptors

### 🔗 Verbindungs-Metriken
- **WebSocket Verbindungsdauer** - Dauer der aktuellen Verbindung
- **Letzter Coin Timestamp** - Zeitpunkt des letzten empfangenen Coins
- **Uptime** - Service-Uptime in Sekunden

## 🎨 Features

- ✅ **Auto-Refresh:** Dashboard aktualisiert sich alle 10 Sekunden
- ✅ **Zeitbereich:** Standardmäßig letzte Stunde, anpassbar
- ✅ **Farbcodierung:** 
  - 🟢 Grün = Gut
  - 🟡 Gelb = Warnung
  - 🔴 Rot = Kritisch
- ✅ **Thresholds:** Automatische Warnungen bei kritischen Werten
- ✅ **Legenden:** Detaillierte Statistiken (Last, Max, Mean, p95, p99)

## 📝 Prometheus Queries

Das Dashboard verwendet folgende Prometheus-Queries:

### Rates (pro Sekunde)
```promql
rate(pumpfun_coins_received_total[5m])
rate(pumpfun_coins_sent_total[5m])
rate(pumpfun_batches_sent_total[5m])
```

### Histogram-Quantile (Latency)
```promql
histogram_quantile(0.50, rate(pumpfun_batch_send_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(pumpfun_batch_send_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(pumpfun_batch_send_duration_seconds_bucket[5m]))
```

### System-Metriken
```promql
process_resident_memory_bytes
process_virtual_memory_bytes
rate(process_cpu_seconds_total[5m]) * 100
```

## 🔧 Anpassungen

### Refresh-Intervall ändern
Im Dashboard-JSON: `"refresh": "10s"` anpassen

### Zeitbereich ändern
Im Dashboard-JSON: `"time": { "from": "now-1h", "to": "now" }` anpassen

### Thresholds anpassen
In den Panel-Konfigurationen unter `fieldConfig.defaults.thresholds`

## 🚨 Alerts (Optional)

Du kannst Alerts hinzufügen für:
- WebSocket Disconnect (`pumpfun_ws_connected == 0`)
- n8n nicht verfügbar (`pumpfun_n8n_available == 0`)
- Hohe Latency (`pumpfun_batch_send_duration_seconds p95 > 1.0`)
- Viele Reconnects (`rate(pumpfun_ws_reconnects_total[5m]) > 0.1`)

## 📚 Weitere Informationen

- **Prometheus Metrics Endpoint:** `http://localhost:8010/metrics`
- **Health Check:** `http://localhost:8010/health`
- **Dokumentation:** Siehe `README.md` im Hauptverzeichnis

---

**Erstellt:** 2025-12-26  
**Version:** 1.0  
**Grafana Version:** 10.0.0+


