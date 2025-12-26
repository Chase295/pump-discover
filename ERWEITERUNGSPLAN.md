# 🚀 Erweiterungsplan: KI-optimierte Rug-Detection Features

## 📋 Übersicht

Dieser Plan beschreibt die Implementierung von 3 neuen Features zur Verbesserung der Rug-Detection durch KI:

1. **Lazy Scam Detektor (Bild-Hash)**
2. **RugCheck Details (Erweiterte Flags)**
3. **Social Effort Metrik**

---

## 1️⃣ Lazy Scam Detektor (Bild-Hash)

### 🎯 Ziel
Erkenne Coins, die dasselbe Bild wie bereits bekannte Rugs verwenden.

### 📊 Implementierung

#### **Schritt 1: SQL-Schema erweitern**
```sql
ALTER TABLE discovered_coins ADD COLUMN image_hash VARCHAR(64);
CREATE INDEX idx_dc_image_hash ON discovered_coins(image_hash);
```

#### **Schritt 2: pHash-Berechnung**

**Option A: Im Python-Relay (Empfohlen für Performance)**
- Vorteil: Schnell, keine zusätzliche API-Calls
- Nachteil: Benötigt `imagehash` Library
- Implementierung: pHash direkt im Relay berechnen, wenn `image_url` vorhanden

**Option B: In n8n (Flexibler)**
- Vorteil: Keine zusätzlichen Dependencies im Relay
- Nachteil: Zusätzlicher HTTP-Request pro Bild
- Implementierung: n8n HTTP-Request → pHash-Service oder Python-Script

**Empfehlung:** Option A (im Relay), da:
- Performance: pHash-Berechnung ist schnell (~50-100ms)
- Keine zusätzlichen API-Calls nötig
- Bild bereits im WebSocket-Event vorhanden

#### **Schritt 3: Datenfluss**

```
WebSocket Event (image_url)
    ↓
Relay: pHash berechnen (wenn image_url vorhanden)
    ↓
n8n: image_hash mit übergeben
    ↓
Datenbank: image_hash speichern
    ↓
KI-Analyse: "Wenn Hash = X und letzte 50 Coins mit diesem Hash waren Rugs → Rug-Wahrscheinlichkeit = 99%"
```

#### **Schritt 4: Was wird an n8n gesendet?**

**Im Relay berechnet:**
```json
{
  "mint": "...",
  "image_url": "https://...",
  "image_hash": "a1b2c3d4e5f6..."  // ← NEU: pHash (64 Zeichen)
}
```

**In n8n:**
- `image_hash` direkt in DB speichern
- Optional: Vergleich mit historischen Hashes (SQL-Query)

---

## 2️⃣ RugCheck Details (Erweiterte Flags)

### 🎯 Ziel
Nicht nur den `risk_score` speichern, sondern auch konkrete Boolean-Flags für harte Ausschlusskriterien.

### 📊 Implementierung

#### **Schritt 1: SQL-Schema erweitern**
```sql
ALTER TABLE discovered_coins ADD COLUMN metadata_is_mutable BOOLEAN;
ALTER TABLE discovered_coins ADD COLUMN mint_authority_enabled BOOLEAN;

CREATE INDEX idx_dc_metadata_mutable ON discovered_coins(metadata_is_mutable);
CREATE INDEX idx_dc_mint_authority ON discovered_coins(mint_authority_enabled);
```

#### **Schritt 2: Datenquelle**

**Quelle:** RugCheck API (wird bereits in n8n abgerufen)

**API-Response (Beispiel):**
```json
{
  "token": {...},
  "metadata": {
    "isMutable": true  // ← metadata_is_mutable
  },
  "mintAuthority": {
    "enabled": true    // ← mint_authority_enabled
  }
}
```

#### **Schritt 3: Datenfluss**

```
Relay: Sendet mint + image_url an n8n
    ↓
n8n: Ruft RugCheck API auf
    ↓
RugCheck API: Liefert metadata.isMutable + mintAuthority.enabled
    ↓
n8n: Speichert beide Flags in DB
    ↓
KI-Analyse: 
  - "Wenn mint_authority_enabled = true → Rug-Wahrscheinlichkeit = 99%"
  - "Wenn metadata_is_mutable = true → Soft-Rug-Wahrscheinlichkeit = 70%"
```

#### **Schritt 4: Was wird an n8n gesendet?**

**Vom Relay:**
```json
{
  "mint": "...",
  "image_url": "..."
  // metadata_is_mutable und mint_authority_enabled werden NICHT vom Relay gesendet,
  // sondern in n8n aus der RugCheck API geholt
}
```

**In n8n:**
- RugCheck API abrufen
- `metadata.isMutable` → `metadata_is_mutable`
- `mintAuthority.enabled` → `mint_authority_enabled`
- Beide Flags in DB speichern

---

## 3️⃣ Social Effort Metrik

### 🎯 Ziel
Einfache Metrik für KI: "Coins mit Social Count < 2 ruggen zu 80% schneller."

### 📊 Implementierung

#### **Schritt 1: SQL-Schema erweitern**
```sql
ALTER TABLE discovered_coins ADD COLUMN social_count INT DEFAULT 0;
CREATE INDEX idx_dc_social_count ON discovered_coins(social_count);
```

#### **Schritt 2: Berechnung**

**Logik:**
```python
social_count = 0
if twitter_url: social_count += 1
if telegram_url: social_count += 1
if website_url: social_count += 1
if discord_url: social_count += 1
# Maximal 4 (alle 4 vorhanden)
```

#### **Schritt 3: Datenfluss**

```
WebSocket Event (metadata mit URLs)
    ↓
Relay: social_count berechnen (0-4)
    ↓
n8n: social_count mit übergeben
    ↓
Datenbank: social_count speichern
    ↓
KI-Analyse: "Wenn social_count < 2 → Rug-Wahrscheinlichkeit = 80%"
```

#### **Schritt 4: Was wird an n8n gesendet?**

**Im Relay berechnet:**
```json
{
  "mint": "...",
  "twitter_url": "https://twitter.com/...",
  "telegram_url": "https://t.me/...",
  "website_url": "https://...",
  "discord_url": null,
  "social_count": 3  // ← NEU: Anzahl vorhandener Social-Links (0-4)
}
```

**In n8n:**
- `social_count` direkt in DB speichern
- Optional: Filterung nach `social_count < 2` für schnelle Rug-Erkennung

---

## 📝 Zusammenfassung: Was wird wo gemacht?

### ✅ **Im Python-Relay berechnet:**
1. `image_hash` (pHash des Bildes) - **wenn image_url vorhanden**
2. `social_count` (Anzahl Social-Links: 0-4) - **immer**

### ⚠️ **In n8n abgerufen (aus RugCheck API):**
1. `metadata_is_mutable` (aus `metadata.isMutable`)
2. `mint_authority_enabled` (aus `mintAuthority.enabled`)

### 📤 **Was wird an n8n gesendet?**

**Erweiterte Payload-Struktur:**
```json
{
  "source": "pump_fun_relay",
  "count": 1,
  "timestamp": "2024-12-25T22:00:00Z",
  "data": [
    {
      // Alle bisherigen WebSocket-Felder
      "mint": "...",
      "name": "...",
      "symbol": "...",
      "image_url": "...",
      "twitter_url": "...",
      "telegram_url": "...",
      "website_url": "...",
      "discord_url": "...",
      
      // NEU: Vom Relay berechnet
      "image_hash": "a1b2c3d4e5f6...",  // pHash (64 Zeichen) oder null
      "social_count": 3,                 // 0-4
      
      // Bereits vorhanden
      "price_sol": 3.46e-8,
      "pool_address": "..."
    }
  ]
}
```

### 🗄️ **Was wird in der Datenbank gespeichert?**

**Neue Spalten:**
- `image_hash VARCHAR(64)` - pHash des Bildes
- `metadata_is_mutable BOOLEAN` - Kann Dev Metadata ändern?
- `mint_authority_enabled BOOLEAN` - Kann Dev neue Tokens drucken?
- `social_count INT` - Anzahl Social-Links (0-4)

---

## 🔧 Technische Details

### pHash-Berechnung (Option A: Im Relay)

**Dependencies:**
```bash
pip install imagehash pillow
```

**Python-Code:**
```python
import imagehash
from PIL import Image
import aiohttp

async def calculate_image_hash(session, image_url):
    """Berechnet pHash eines Bildes"""
    try:
        async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                image_data = await resp.read()
                image = Image.open(io.BytesIO(image_data))
                phash = imagehash.phash(image)
                return str(phash)  # z.B. "a1b2c3d4e5f6..."
    except Exception as e:
        return None  # Fehler → kein Hash
```

**Performance:**
- ~50-100ms pro Bild
- Asynchron → kein Blocking
- Optional: Caching für wiederholte URLs

### Social Count Berechnung

**Python-Code:**
```python
def calculate_social_count(data):
    """Berechnet Social Count (0-4)"""
    count = 0
    if data.get("twitter_url"):
        count += 1
    if data.get("telegram_url"):
        count += 1
    if data.get("website_url"):
        count += 1
    if data.get("discord_url"):
        count += 1
    return count
```

---

## 📅 Implementierungsreihenfolge

1. ✅ **SQL-Schema erweitern** (4 neue Spalten + Indexe)
2. ✅ **Relay-Script erweitern** (social_count berechnen, image_hash optional)
3. ✅ **n8n Workflow anpassen** (metadata_is_mutable + mint_authority_enabled aus API holen)
4. ✅ **UI Informationsseite erweitern** (neue Felder dokumentieren)

---

## 🎯 KI-Lernziele

Nach Implementierung kann die KI lernen:

1. **Bild-Hash Pattern:**
   - "Wenn `image_hash = X` und letzte 50 Coins mit diesem Hash waren Rugs → Rug-Wahrscheinlichkeit = 99%"

2. **Mint Authority:**
   - "Wenn `mint_authority_enabled = true` → Rug-Wahrscheinlichkeit = 99% (hartes Ausschlusskriterium)"

3. **Metadata Mutable:**
   - "Wenn `metadata_is_mutable = true` → Soft-Rug-Wahrscheinlichkeit = 70%"

4. **Social Effort:**
   - "Wenn `social_count < 2` → Rug-Wahrscheinlichkeit = 80%"
   - "Wenn `social_count >= 3` → Rug-Wahrscheinlichkeit = 20%"

---

## ✅ Checkliste

- [ ] SQL-Schema erweitert (4 neue Spalten)
- [ ] Relay-Script: `social_count` berechnen
- [ ] Relay-Script: `image_hash` berechnen (optional, wenn image_url vorhanden)
- [ ] n8n Workflow: `metadata_is_mutable` aus RugCheck API holen
- [ ] n8n Workflow: `mint_authority_enabled` aus RugCheck API holen
- [ ] UI Informationsseite erweitert
- [ ] Dokumentation aktualisiert

