# 📊 Daten-Mapping: n8n Webhook → SQL Schema

## ✅ Direkt verfügbare Felder vom WebSocket (können sofort gefüllt werden):

### 1. Identifikation
| WebSocket Feld | SQL Feld | Status |
|----------------|----------|--------|
| `mint` | `token_address` | ✅ Direkt |
| `name` | `name` | ✅ Direkt |
| `symbol` | `symbol` | ✅ Direkt |
| `bondingCurveKey` | `bonding_curve_key` | ✅ Direkt |
| `pool` | `pool_type` | ✅ Direkt |

### 1b. Token-Eigenschaften (aus API)
| API Feld | SQL Feld | Status |
|----------|----------|--------|
| `token.decimals` | `token_decimals` | ⚠️ Aus API |
| `token.supply` | `token_supply` | ⚠️ Aus API |
| `deployPlatform` | `deploy_platform` | ⚠️ Aus API |

### 2. Transaktions-Informationen
| WebSocket Feld | SQL Feld | Status |
|----------------|----------|--------|
| `signature` | `signature` | ✅ Direkt |
| `traderPublicKey` | `trader_public_key` | ✅ Direkt |
| `txType` | - | ❌ Nicht benötigt (nur "create") |

### 3. Bonding Curve Details
| WebSocket Feld | SQL Feld | Status |
|----------------|----------|--------|
| `bondingCurveKey` | `bonding_curve_key` | ✅ Direkt |
| `vTokensInBondingCurve` | `v_tokens_in_bonding_curve` | ✅ Direkt |
| `vSolInBondingCurve` | `v_sol_in_bonding_curve` | ✅ Direkt |

### 4. Initial Buy
| WebSocket Feld | SQL Feld | Status |
|----------------|----------|--------|
| `initialBuy` | `initial_buy_tokens` | ✅ Direkt |
| `solAmount` | `initial_buy_sol` | ✅ Direkt |

### 5. Preis & Market Cap
| WebSocket Feld | SQL Feld | Status |
|----------------|----------|--------|
| `marketCapSol` | `market_cap_sol` | ✅ Direkt |
| - | `price_sol` | ⚠️ Berechnet (aus marketCapSol) |
| - | `liquidity_sol` | ✅ Direkt (`vSolInBondingCurve`) |

### 6. Status Flags & Phase
| WebSocket Feld | SQL Feld | Status |
|----------------|----------|--------|
| `is_mayhem_mode` | `is_mayhem_mode` | ✅ Direkt |
| `pool` | `pool_type` | ✅ Direkt |
| `phaseId` | `phase_id` | ✅ Direkt |

### 7. Metadata
| WebSocket Feld | SQL Feld | Status |
|----------------|----------|--------|
| `uri` | `metadata_uri` | ✅ Direkt |

---

## ⚠️ Felder die aus Metadata URI extrahiert werden müssen (in n8n):

### Aus `uri` (IPFS/RapidLaunch) abrufen:
| Metadata Feld | SQL Feld | Status |
|----------------|----------|--------|
| `metadata.description` | `description` | ⚠️ Aus Metadata |
| `metadata.image` | `image_url` | ⚠️ Aus Metadata |
| `metadata.twitter` | `twitter_url` | ⚠️ Aus Metadata |
| `metadata.telegram` | `telegram_url` | ⚠️ Aus Metadata |
| `metadata.website` | `website_url` | ⚠️ Aus Metadata |
| `metadata.discord` | `discord_url` | ⚠️ Aus Metadata |

---

## ❌ Felder die NICHT vom WebSocket kommen (müssen berechnet/ermittelt werden):

### Zeitstempel
| SQL Feld | Quelle |
|----------|--------|
| `discovered_at` | ✅ Auto: `NOW()` |
| `token_created_at` | ⚠️ Aus `signature` Timestamp extrahieren (Solana) |

### Graduation
| SQL Feld | Quelle |
|----------|--------|
| `open_market_cap_sol` | ✅ Default: 85000 |

### Management
| SQL Feld | Quelle |
|----------|--------|
| `blockchain_id` | ✅ Default: 1 (Solana) |
| `pool_address` | ⚠️ Könnte `bonding_curve_key` sein oder separat |
| `is_graduated` | ⚠️ n8n/Update |
| `is_active` | ✅ Default: TRUE |
| `final_outcome` | ✅ Default: 'PENDING' |
| `classification` | ✅ Default: 'UNKNOWN' |
| `status_note` | ⚠️ n8n/Manuell |

### Risiko & Analyse (später)
| SQL Feld | Quelle |
|----------|--------|
| `risk_score` | ⚠️ n8n/KI-Analyse |
| `top_10_holders_pct` | ⚠️ n8n/On-Chain-Analyse |
| `has_socials` | ⚠️ Berechnet in n8n (aus Social URLs) |

---

## 📝 Zusammenfassung

### ✅ Sofort verfügbar (15 Felder):
1. `token_address` ← `mint`
2. `name` ← `name`
3. `symbol` ← `symbol`
4. `signature` ← `signature`
5. `trader_public_key` ← `traderPublicKey`
6. `bonding_curve_key` ← `bondingCurveKey`
7. `pool_type` ← `pool`
8. `v_tokens_in_bonding_curve` ← `vTokensInBondingCurve`
9. `v_sol_in_bonding_curve` ← `vSolInBondingCurve`
10. `initial_buy_tokens` ← `initialBuy`
11. `initial_buy_sol` ← `solAmount`
12. `market_cap_sol` ← `marketCapSol`
13. `liquidity_sol` ← `vSolInBondingCurve`
14. `is_mayhem_mode` ← `is_mayhem_mode`
15. `metadata_uri` ← `uri`

### ⚠️ Aus Metadata URI extrahieren (6 Felder):
16. `description` ← `metadata.description`
17. `image_url` ← `metadata.image`
18. `twitter_url` ← `metadata.twitter`
19. `telegram_url` ← `metadata.telegram`
20. `website_url` ← `metadata.website`
21. `discord_url` ← `metadata.discord`

### ⚠️ Aus API (3 Felder):
22. `token_decimals` ← `api.token.decimals`
23. `token_supply` ← `api.token.supply`
24. `deploy_platform` ← `api.deployPlatform`

### ⚠️ Berechnet/Default (7 Felder):
25. `discovered_at` ← `NOW()`
26. `token_created_at` ← Aus Signature (Solana)
27. `price_sol` ← Berechnet aus `marketCapSol`
28. `open_market_cap_sol` ← Default: 85000
29. `blockchain_id` ← Default: 1
30. `is_active` ← Default: TRUE
31. `final_outcome` ← Default: 'PENDING'

### ❌ Fehlt noch (muss später gefüllt werden):
- `pool_address` (optional, könnte `bonding_curve_key` sein)
- `risk_score` (KI-Analyse)
- `top_10_holders_pct` (On-Chain-Analyse)
- `has_socials` (berechnet)
- `is_graduated` (Update)
- `classification` (KI-Analyse)
- `status_note` (Manuell)

---

## 🎯 n8n Workflow Mapping

### Direktes Mapping (Body → SQL):
```javascript
{
  token_address: $json.body.data[].mint,
  name: $json.body.data[].name,
  symbol: $json.body.data[].symbol,
  signature: $json.body.data[].signature,
  trader_public_key: $json.body.data[].traderPublicKey,
  bonding_curve_key: $json.body.data[].bondingCurveKey,
  pool_type: $json.body.data[].pool,
  v_tokens_in_bonding_curve: $json.body.data[].vTokensInBondingCurve,
  v_sol_in_bonding_curve: $json.body.data[].vSolInBondingCurve,
  initial_buy_tokens: $json.body.data[].initialBuy,
  initial_buy_sol: $json.body.data[].solAmount,
  market_cap_sol: $json.body.data[].marketCapSol,
  liquidity_sol: $json.body.data[].vSolInBondingCurve,
  is_mayhem_mode: $json.body.data[].is_mayhem_mode,
  metadata_uri: $json.body.data[].uri,
  discovered_at: NOW(),
  open_market_cap_sol: 85000,
  blockchain_id: 1,
  is_active: true,
  final_outcome: 'PENDING'
}
```

### API-Daten Mapping (nach Rug-Check in n8n):
```javascript
{
  token_decimals: $json.api_data[].token.decimals,
  token_supply: $json.api_data[].token.supply,
  deploy_platform: $json.api_data[].deployPlatform
}
```

### Metadata-Extraktion (HTTP Request Node):
Für jedes `uri` Feld:
1. HTTP GET Request zu `uri`
2. Parse JSON Response
3. Extrahiere: description, image, twitter, telegram, website, discord

