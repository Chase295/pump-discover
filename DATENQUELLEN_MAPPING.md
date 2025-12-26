# 📊 Datenquellen-Mapping: Wo kommen die Felder her?

## 🔍 Übersicht der 3 Datenquellen

### 1️⃣ WebSocket (create Event) - Erste Datenquelle
### 2️⃣ API (Token-Analyse) - Zweite Datenquelle  
### 3️⃣ Metadata (aus URI) - Dritte Datenquelle

---

## 📋 Feld-für-Feld: Woher kommen die Daten?

### ✅ `token_decimals` (INT)

**Quelle:** API (Datenquelle 2)  
**Pfad:** `token.decimals`

**Beispiel aus deinen Daten:**
```json
{
  "token": {
    "decimals": 6  ← HIER!
  }
}
```

**Mapping in n8n:**
```javascript
token_decimals: $json.api[].token.decimals
```

---

### ✅ `token_supply` (NUMERIC(30, 6))

**Quelle:** API (Datenquelle 2)  
**Pfad:** `token.supply`

**Beispiel aus deinen Daten:**
```json
{
  "token": {
    "supply": 1000000000000000  ← HIER!
  }
}
```

**Mapping in n8n:**
```javascript
token_supply: $json.api[].token.supply
```

**Hinweis:** Das ist die **raw Supply** (mit Decimals). Für UI-Anzeige: `supply / 10^decimals`

---

### ✅ `deploy_platform` (VARCHAR(50))

**Quelle:** API (Datenquelle 2)  
**Pfad:** `deployPlatform`

**Beispiel aus deinen Daten:**
```json
{
  "deployPlatform": "rapidlaunch"  ← HIER!
}
```

**Mapping in n8n:**
```javascript
deploy_platform: $json.api[].deployPlatform
```

---

## 🔄 Vollständiges Mapping für alle 3 Felder

### In n8n Workflow:

**1. WebSocket-Daten empfangen** (vom Relay)
```json
{
  "mint": "...",
  "name": "...",
  "symbol": "...",
  ...
}
```

**2. API-Daten abrufen** (HTTP Request zu Token-Analyse-API)
```json
{
  "mint": "...",
  "token": {
    "decimals": 6,        ← token_decimals
    "supply": 1000000000000000  ← token_supply
  },
  "deployPlatform": "rapidlaunch"  ← deploy_platform
}
```

**3. Metadata abrufen** (HTTP Request zu URI)
```json
{
  "name": "...",
  "description": "...",
  ...
}
```

**4. In Datenbank speichern:**
```sql
INSERT INTO discovered_coins (
  token_address,
  token_decimals,      -- ← Aus API: token.decimals
  token_supply,        -- ← Aus API: token.supply
  deploy_platform,     -- ← Aus API: deployPlatform
  ...
) VALUES (
  $1, $2, $3, $4, ...
);
```

---

## 🎯 Zusammenfassung

| Feld | Quelle | JSON-Pfad | Verfügbar? |
|------|--------|-----------|------------|
| `token_decimals` | API | `token.decimals` | ✅ Ja |
| `token_supply` | API | `token.supply` | ✅ Ja |
| `deploy_platform` | API | `deployPlatform` | ✅ Ja |

**Alle 3 Felder kommen aus der API (zweite Datenquelle)!**

---

## 💡 Wichtiger Hinweis

Die API-Daten müssen **separat abgerufen werden** in n8n:
- Du bekommst vom Relay nur die WebSocket-Daten
- Die API-Daten musst du mit einem **HTTP Request Node** in n8n abrufen
- API-Endpoint: Wahrscheinlich etwas wie `https://api.example.com/token/{mint}`

**Frage:** Hast du bereits einen API-Endpoint, um diese Token-Daten abzurufen? Oder kommen die API-Daten auch vom Relay?

