# 🔄 Relay-Erweiterung: Alle Daten an n8n senden

## 🎯 Ziel

Der Relay-Service soll **ALLE verfügbaren Informationen** pro Coin an n8n senden:
1. ✅ WebSocket-Daten (bereits vorhanden)
2. ⚠️ API-Daten (Token-Analyse) - **muss hinzugefügt werden**
3. ⚠️ Metadata-Daten (aus URI) - **muss hinzugefügt werden**

---

## 📊 Aktueller Stand

**Was wird aktuell gesendet:**
- Nur WebSocket-Daten (create Event)
- Berechnete Felder: `price_sol`, `pool_address`

**Was fehlt:**
- API-Daten (Token-Analyse mit `token.decimals`, `token.supply`, `deployPlatform`, etc.)
- Metadata-Daten (aus URI: `description`, `image`, `twitter`, etc.)

---

## 🔧 Vorschlag: Erweiterte Datenstruktur

### Option 1: Alles in einem erweiterten Payload (Empfohlen)

**Payload-Struktur:**
```json
{
  "source": "pump_fun_relay",
  "count": 1,
  "timestamp": "2024-12-25T22:00:00Z",
  "data": [
    {
      // WebSocket-Daten (wie bisher)
      "signature": "...",
      "mint": "...",
      "name": "...",
      "symbol": "...",
      "price_sol": 3.46e-8,
      "pool_address": "...",
      ...
      
      // NEU: API-Daten (wenn verfügbar)
      "api_data": {
        "token": {
          "decimals": 6,
          "supply": 1000000000000000
        },
        "creatorBalance": 0,
        "totalHolders": 1,
        "rugged": false,
        "deployPlatform": "rapidlaunch",
        "classification": "WARNING",
        "score_normalised": 1,
        "topHolders": [...]
      },
      
      // NEU: Metadata-Daten (wenn verfügbar)
      "metadata": {
        "description": "...",
        "image": "...",
        "twitter": "...",
        "telegram": "...",
        "website": "..."
      }
    }
  ]
}
```

---

## 🛠️ Implementierung

### Schritt 1: API-Daten abrufen

**Frage:** Welche API verwendest du für Token-Analyse?
- RugCheck API?
- Solana Tracker API?
- Andere API?

**Beispiel-Implementierung:**
```python
async def fetch_api_data(session, mint_address):
    """Ruft Token-Analyse-Daten von API ab"""
    api_url = f"https://api.example.com/tokens/{mint_address}"
    try:
        async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        return None
```

### Schritt 2: Metadata abrufen

```python
async def fetch_metadata(session, uri):
    """Ruft Metadata von URI ab"""
    if not uri:
        return None
    try:
        async with session.get(uri, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        return None
```

### Schritt 3: Daten zusammenführen

```python
# Für jeden Coin im Buffer:
for coin in buffer:
    mint = coin.get("mint")
    uri = coin.get("uri")
    
    # API-Daten abrufen (parallel)
    api_data = await fetch_api_data(session, mint)
    if api_data:
        coin["api_data"] = api_data
    
    # Metadata abrufen (parallel)
    metadata = await fetch_metadata(session, uri)
    if metadata:
        coin["metadata"] = metadata
```

---

## ⚙️ Konfiguration

**Neue Environment-Variablen:**
```bash
# API-Konfiguration
TOKEN_API_URL=https://api.example.com/tokens/{mint}
TOKEN_API_ENABLED=true
TOKEN_API_TIMEOUT=5

# Metadata-Konfiguration
METADATA_FETCH_ENABLED=true
METADATA_TIMEOUT=5
```

---

## ⚠️ Überlegungen

### Performance
- **API-Aufrufe** können langsam sein (5-10s pro Request)
- **Lösung:** Parallel abrufen mit `asyncio.gather()`
- **Alternative:** API-Aufrufe in n8n machen (nicht im Relay)

### Rate-Limiting
- APIs haben oft Rate-Limits
- **Lösung:** Retry-Logik mit Backoff
- **Alternative:** API-Aufrufe in n8n (mehr Kontrolle)

### Fehlerbehandlung
- Was passiert, wenn API nicht erreichbar ist?
- **Lösung:** API-Daten optional machen (nur WebSocket-Daten senden)

---

## 💡 Empfehlung

### Option A: API-Aufrufe im Relay (Vollständige Daten)
- ✅ Alle Daten in einem Payload
- ✅ n8n bekommt alles fertig
- ❌ Langsamer (API-Aufrufe pro Coin)
- ❌ Komplexere Fehlerbehandlung

### Option B: API-Aufrufe in n8n (Modular)
- ✅ Schneller (Relay sendet nur WebSocket-Daten)
- ✅ Mehr Kontrolle in n8n
- ✅ Einfacher zu debuggen
- ❌ n8n muss API-Aufrufe machen

---

## ❓ Fragen

1. **Welche API verwendest du für Token-Analyse?**
   - URL/Endpoint?
   - Benötigt API-Key?
   - Rate-Limits?

2. **Soll der Relay die API-Daten abrufen oder n8n?**
   - Relay: Alles in einem Payload
   - n8n: Modular, mehr Kontrolle

3. **Wie wichtig ist Performance?**
   - Schnell: API-Aufrufe in n8n
   - Vollständig: API-Aufrufe im Relay

---

## 🚀 Nächste Schritte

Sobald du die Fragen beantwortet hast, kann ich:
1. ✅ Den Relay-Code erweitern
2. ✅ API-Integration implementieren
3. ✅ Metadata-Fetch hinzufügen
4. ✅ Fehlerbehandlung verbessern
5. ✅ Konfiguration hinzufügen

