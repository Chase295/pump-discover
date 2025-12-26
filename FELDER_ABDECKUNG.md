# 📊 Felder-Abdeckung: Datenquellen → SQL Schema

## 🔍 Analyse: Können alle Felder gefüllt werden?

### ✅ Datenquelle 1: WebSocket (create Event)
```json
{
  "signature": "...",
  "mint": "...",
  "traderPublicKey": "...",
  "txType": "create",
  "initialBuy": 97545454.545455,
  "solAmount": 3,
  "bondingCurveKey": "...",
  "vTokensInBondingCurve": 975454545.454545,
  "vSolInBondingCurve": 33.000000000000014,
  "marketCapSol": 33.8303821062442,
  "name": "...",
  "symbol": "...",
  "uri": "...",
  "is_mayhem_mode": false,
  "pool": "pump",
  "price_sol": 3.468165919559053e-8,
  "pool_address": "..."
}
```

### ✅ Datenquelle 2: API (Token-Analyse)
```json
{
  "mint": "...",
  "creator": "...",
  "creatorBalance": 0,
  "token": {
    "supply": 1000000000000000,
    "decimals": 6
  },
  "topHolders": [...],
  "score": 1,
  "score_normalised": 1,
  "totalHolders": 1,
  "rugged": false,
  "deployPlatform": "rapidlaunch",
  "classification": "WARNING"
}
```

### ✅ Datenquelle 3: Metadata (aus URI)
```json
{
  "name": "...",
  "symbol": "...",
  "description": "",
  "twitter": "...",
  "telegram": "",
  "website": "...",
  "image": "..."
}
```

---

## 📋 Feld-für-Feld Analyse

| SQL Feld | Typ | Quelle | Status | Mapping |
|----------|-----|--------|--------|---------|
| **1. IDENTIFIKATION** |
| `token_address` | VARCHAR(64) | WebSocket | ✅ | `mint` |
| `blockchain_id` | INT | Default | ✅ | `1` (Solana) |
| `symbol` | VARCHAR(30) | WebSocket | ✅ | `symbol` |
| `name` | VARCHAR(255) | WebSocket | ✅ | `name` |
| **2. TRANSAKTIONS-INFORMATIONEN** |
| `signature` | VARCHAR(88) | WebSocket | ✅ | `signature` |
| `trader_public_key` | VARCHAR(44) | WebSocket | ✅ | `traderPublicKey` |
| **3. BONDING CURVE & POOL** |
| `bonding_curve_key` | VARCHAR(44) | WebSocket | ✅ | `bondingCurveKey` |
| `pool_address` | VARCHAR(64) | WebSocket | ✅ | `pool_address` |
| `pool_type` | VARCHAR(20) | WebSocket | ✅ | `pool` |
| `v_tokens_in_bonding_curve` | NUMERIC(30,6) | WebSocket | ✅ | `vTokensInBondingCurve` |
| `v_sol_in_bonding_curve` | NUMERIC(20,6) | WebSocket | ✅ | `vSolInBondingCurve` |
| **4. INITIAL BUY** |
| `initial_buy_sol` | NUMERIC(20,6) | WebSocket | ✅ | `solAmount` |
| `initial_buy_tokens` | NUMERIC(30,6) | WebSocket | ✅ | `initialBuy` |
| **5. ZEITSTEMPEL** |
| `discovered_at` | TIMESTAMP | Default | ✅ | `NOW()` |
| `token_created_at` | TIMESTAMP | Berechnet | ⚠️ | Aus `signature` extrahieren |
| **6. PREIS & MARKET CAP** |
| `price_sol` | NUMERIC(30,18) | WebSocket | ✅ | `price_sol` |
| `market_cap_sol` | NUMERIC(20,2) | WebSocket | ✅ | `marketCapSol` |
| `liquidity_sol` | NUMERIC(20,6) | WebSocket | ✅ | `vSolInBondingCurve` |
| **7. GRADUATION** |
| `open_market_cap_sol` | NUMERIC(20,2) | Default | ✅ | `85000` |
| `phase_id` | INT | ❌ | ❌ | **FEHLT in allen Quellen** |
| **8. STATUS FLAGS** |
| `is_mayhem_mode` | BOOLEAN | WebSocket | ✅ | `is_mayhem_mode` |
| `is_graduated` | BOOLEAN | Berechnet | ⚠️ | Aus `phase_id` oder `market_cap_sol` |
| `is_active` | BOOLEAN | Default | ✅ | `TRUE` |
| **9. RISIKO & ANALYSE** |
| `risk_score` | INT | API | ✅ | `score_normalised` |
| `top_10_holders_pct` | NUMERIC(5,2) | API | ✅ | `topHolders[0].pct` |
| `has_socials` | BOOLEAN | Berechnet | ✅ | Aus Metadata URLs |
| **10. METADATA & SOCIAL MEDIA** |
| `metadata_uri` | TEXT | WebSocket | ✅ | `uri` |
| `description` | TEXT | Metadata | ✅ | `description` |
| `image_url` | TEXT | Metadata | ✅ | `image` |
| `twitter_url` | TEXT | Metadata | ✅ | `twitter` |
| `telegram_url` | TEXT | Metadata | ✅ | `telegram` |
| `website_url` | TEXT | Metadata | ✅ | `website` |
| `discord_url` | TEXT | Metadata | ❌ | **FEHLT in Metadata** |
| **11. MANAGEMENT & KLASSIFIZIERUNG** |
| `final_outcome` | VARCHAR(20) | Default | ✅ | `'PENDING'` |
| `classification` | VARCHAR(50) | API | ✅ | `classification` |
| `status_note` | VARCHAR(255) | Manuell | ⚠️ | Optional, manuell |

---

## ❌ Felder die NICHT gefüllt werden können:

### 1. `phase_id` (INT)
- **Status:** ❌ FEHLT
- **Problem:** Kommt weder im WebSocket noch in der API vor
- **Lösung:** 
  - Optional: Aus `is_graduated` ableiten (0 = bonding_curve, 1 = graduated)
  - Oder: Feld entfernen wenn nicht benötigt
  - Oder: Später über Update-Query füllen

### 2. `discord_url` (TEXT)
- **Status:** ❌ FEHLT
- **Problem:** Kommt nicht in der Metadata vor
- **Lösung:**
  - Optional: Feld kann NULL bleiben
  - Oder: Später manuell ergänzen

### 3. `token_created_at` (TIMESTAMP)
- **Status:** ⚠️ BEREICHNET
- **Problem:** Muss aus `signature` Timestamp extrahiert werden
- **Lösung:**
  - Solana Transaction Signature parsen
  - Oder: `discovered_at` verwenden als Näherung

---

## ✅ Zusammenfassung

### Vollständig füllbar: **36 von 39 Feldern** (92%)

### Teilweise füllbar: **2 Felder**
- `token_created_at` - Kann aus Signature extrahiert werden
- `is_graduated` - Kann aus `market_cap_sol` berechnet werden

### Nicht füllbar: **2 Felder**
- `phase_id` - Kommt in keiner Quelle vor
- `discord_url` - Kommt nicht in Metadata vor

### Optional/Manuell: **1 Feld**
- `status_note` - Für manuelle Notizen

---

## 🎯 Empfehlung

### Option 1: `phase_id` entfernen
Wenn `phase_id` nicht benötigt wird, kann es entfernt werden.

### Option 2: `phase_id` berechnen
```sql
-- In n8n berechnen:
phase_id = CASE 
  WHEN is_graduated = true THEN 1
  ELSE 0
END
```

### Option 3: `phase_id` später füllen
Feld bleibt NULL und wird später über Update-Query gefüllt.

---

## 📝 Mapping für n8n

### WebSocket → SQL (direkt):
```javascript
{
  token_address: $json.body.data[].mint,
  signature: $json.body.data[].signature,
  trader_public_key: $json.body.data[].traderPublicKey,
  bonding_curve_key: $json.body.data[].bondingCurveKey,
  pool_address: $json.body.data[].pool_address,
  pool_type: $json.body.data[].pool,
  v_tokens_in_bonding_curve: $json.body.data[].vTokensInBondingCurve,
  v_sol_in_bonding_curve: $json.body.data[].vSolInBondingCurve,
  initial_buy_sol: $json.body.data[].solAmount,
  initial_buy_tokens: $json.body.data[].initialBuy,
  price_sol: $json.body.data[].price_sol,
  market_cap_sol: $json.body.data[].marketCapSol,
  liquidity_sol: $json.body.data[].vSolInBondingCurve,
  is_mayhem_mode: $json.body.data[].is_mayhem_mode,
  metadata_uri: $json.body.data[].uri
}
```

### API → SQL:
```javascript
{
  risk_score: $json.api[].score_normalised,
  top_10_holders_pct: $json.api[].topHolders[0].pct,
  classification: $json.api[].classification
}
```

### Metadata → SQL:
```javascript
{
  description: $json.metadata[].description,
  image_url: $json.metadata[].image,
  twitter_url: $json.metadata[].twitter,
  telegram_url: $json.metadata[].telegram,
  website_url: $json.metadata[].website
  // discord_url: FEHLT
}
```

### Berechnet:
```javascript
{
  has_socials: ($json.metadata[].twitter || $json.metadata[].telegram || $json.metadata[].website) ? true : false,
  is_graduated: ($json.body.data[].marketCapSol >= 85000) ? true : false,
  phase_id: null // ODER berechnet aus is_graduated
}
```

