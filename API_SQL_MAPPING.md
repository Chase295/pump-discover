# 🔗 API → SQL Feld-Mapping (RugCheck API)

## 📊 Direktes Mapping für n8n

### API JSON → SQL Feld-Namen

| API Feld | SQL Feld | Typ | Beispiel | Hinweis |
|----------|----------|-----|----------|---------|
| `token.decimals` | `token_decimals` | INT | `6` | ✅ Statisch |
| `token.supply` | `token_supply` | NUMERIC(30, 6) | `1000000000000000` | ✅ Statisch (raw, mit decimals) |
| `deployPlatform` | `deploy_platform` | VARCHAR(50) | `"unknown"` | ✅ Statisch |
| `score` oder `score_normalised` | `risk_score` | INT | `1` | ⚠️ Kann sich ändern, aber initial wichtig |
| `rugged` | - | - | `false` | ❌ Nicht im Schema (könnte für `final_outcome` verwendet werden) |
| `totalHolders` | - | - | `3` | ❌ Nicht im Schema (wird in Metriken-Tabelle gespeichert) |
| `creatorBalance` | - | - | `66285714223523` | ❌ Nicht im Schema (wird in Metriken-Tabelle gespeichert) |
| `topHolders` | `top_10_holders_pct` | NUMERIC(5, 2) | - | ⚠️ Muss berechnet werden (ist `null` in deinem Beispiel) |
| `tokenMeta.uri` | `metadata_uri` | TEXT | - | ✅ Bereits vom WebSocket, aber auch hier verfügbar |
| `launchpad.platform` | - | - | `"pump_fun"` | ℹ️ Info, aber nicht im Schema |

---

## ✅ **Empfohlene Felder für `discovered_coins` Tabelle:**

### 1. **Statische Felder (MÜSSEN gespeichert werden):**

```javascript
{
  // Identifikation
  token_decimals: $json[].token.decimals,           // 6
  token_supply: $json[].token.supply,               // 1000000000000000
  deploy_platform: $json[].deployPlatform,           // "unknown"
  
  // Risiko (initial)
  risk_score: $json[].score_normalised || $json[].score,  // 1
}
```

### 2. **Berechnete Felder (optional):**

```javascript
{
  // Top 10 Holders Prozent (muss aus topHolders Array berechnet werden)
  top_10_holders_pct: calculateTop10HoldersPct($json[].topHolders),
  
  // Has Socials (aus Metadata URI geparst)
  has_socials: hasSocialMediaLinks($json[].tokenMeta.uri),
}
```

### 3. **Felder die NICHT in `discovered_coins` gehören:**

Diese Felder ändern sich dynamisch und gehören in die **Metriken-Tabelle** (die du alle 5 Sekunden aktualisierst):

- ❌ `totalHolders` → Metriken-Tabelle
- ❌ `creatorBalance` → Metriken-Tabelle  
- ❌ `rugged` → Metriken-Tabelle (oder `final_outcome` updaten)
- ❌ `price` → Metriken-Tabelle
- ❌ `totalMarketLiquidity` → Metriken-Tabelle
- ❌ `totalStableLiquidity` → Metriken-Tabelle

---

## 📝 n8n Mapping (JavaScript)

### Für jeden Token aus der API-Antwort:

```javascript
{
  // Statische Token-Informationen
  token_decimals: $json[].token.decimals,
  token_supply: $json[].token.supply,
  deploy_platform: $json[].deployPlatform || "unknown",
  
  // Initialer Risiko-Score
  risk_score: $json[].score_normalised || $json[].score || null,
  
  // Optional: Top 10 Holders Prozent (wenn topHolders Array vorhanden)
  top_10_holders_pct: $json[].topHolders 
    ? calculateTop10HoldersPercentage($json[].topHolders) 
    : null,
  
  // Optional: Has Socials (wenn Metadata URI geparst wird)
  has_socials: $json[].tokenMeta.uri 
    ? await checkSocialMediaLinks($json[].tokenMeta.uri)
    : false
}
```

---

## 🔄 Vollständige Mapping-Liste

### ✅ **Direkt aus API (4 Felder):**

1. `token.decimals` → `token_decimals` ✅
2. `token.supply` → `token_supply` ✅
3. `deployPlatform` → `deploy_platform` ✅
4. `score` / `score_normalised` → `risk_score` ✅

### ⚠️ **Berechnet aus API (2 Felder):**

5. `topHolders[]` → `top_10_holders_pct` (muss berechnet werden)
6. `tokenMeta.uri` → `has_socials` (muss geparst werden)

### ❌ **NICHT für `discovered_coins` (gehören in Metriken-Tabelle):**

- `totalHolders` → Metriken-Tabelle
- `creatorBalance` → Metriken-Tabelle
- `rugged` → Metriken-Tabelle oder `final_outcome` updaten
- `price` → Metriken-Tabelle
- `totalMarketLiquidity` → Metriken-Tabelle
- `totalStableLiquidity` → Metriken-Tabelle
- `markets[]` → Metriken-Tabelle
- `detectedAt` → Metriken-Tabelle (oder `token_created_at`)

---

## 💡 **Empfehlung für n8n Workflow:**

### Schritt 1: API-Daten abrufen
```javascript
// HTTP Request Node
GET https://api.rugcheck.xyz/v1/tokens/{mint}
```

### Schritt 2: Mapping zu SQL-Feldern
```javascript
{
  token_decimals: $json.token.decimals,
  token_supply: $json.token.supply,
  deploy_platform: $json.deployPlatform || "unknown",
  risk_score: $json.score_normalised || $json.score || null
}
```

### Schritt 3: Optional - Top 10 Holders berechnen
```javascript
// Function Node
const topHolders = $json.topHolders || [];
if (topHolders.length > 0) {
  const top10 = topHolders.slice(0, 10);
  const top10Total = top10.reduce((sum, h) => sum + (h.amount || 0), 0);
  const totalSupply = $json.token.supply;
  return (top10Total / totalSupply) * 100;
}
return null;
```

### Schritt 4: In Datenbank speichern
```sql
UPDATE discovered_coins SET
  token_decimals = $1,
  token_supply = $2,
  deploy_platform = $3,
  risk_score = $4,
  top_10_holders_pct = $5
WHERE token_address = $6;
```

---

## ✅ **Zusammenfassung**

**Von deiner API-Antwort brauchst du für `discovered_coins`:**

✅ **4 Felder direkt:**
- `token_decimals` ← `token.decimals`
- `token_supply` ← `token.supply`
- `deploy_platform` ← `deployPlatform`
- `risk_score` ← `score` oder `score_normalised`

⚠️ **2 Felder berechnet (optional):**
- `top_10_holders_pct` ← aus `topHolders[]` berechnet
- `has_socials` ← aus `tokenMeta.uri` geparst

❌ **NICHT für `discovered_coins` (gehören in Metriken-Tabelle):**
- `totalHolders`, `creatorBalance`, `rugged`, `price`, etc.

**Insgesamt: 4-6 Felder aus der API für den initialen Snapshot!**


