# 🔗 WebSocket → SQL Feld-Mapping

## 📊 Direktes Mapping für n8n

### WebSocket JSON → SQL Feld-Namen

| WebSocket Feld | SQL Feld | Typ | Beispiel |
|----------------|----------|-----|----------|
| `signature` | `signature` | VARCHAR(88) | "UEFn9JFNHYaUVDvmq66EBPFVKENsP4bS1Q75hXkvzQgWbKnKWdymxnRE3RZeG23Fm1AXwL1FByK59mdRioC4o7H" |
| `mint` | `token_address` | VARCHAR(64) | "7GggZA5GEHqTyiuFBTsWiU5uz7HDvSBMH11UB8GDpump" |
| `traderPublicKey` | `trader_public_key` | VARCHAR(44) | "DxGLoNf279eyYqTRTYqPZTtiB5BbF4fqRtfjfrvQyiwt" |
| `txType` | - | - | "create" (wird nicht gespeichert) |
| `initialBuy` | `initial_buy_tokens` | NUMERIC(30, 6) | 66285714.223523 |
| `solAmount` | `initial_buy_sol` | NUMERIC(20, 6) | 1.97530864 |
| `bondingCurveKey` | `bonding_curve_key` | VARCHAR(44) | "BMyRVLmarQUvTJ7YwkH3cQsg1VgSX3fV6AKgSYNb1joR" |
| `vTokensInBondingCurve` | `v_tokens_in_bonding_curve` | NUMERIC(30, 6) | 1006714285.776477 |
| `vSolInBondingCurve` | `v_sol_in_bonding_curve` | NUMERIC(20, 6) | 31.975308639999987 |
| `marketCapSol` | `market_cap_sol` | NUMERIC(20, 2) | 31.762049165059267 |
| `name` | `name` | VARCHAR(255) | "wifmas" |
| `symbol` | `symbol` | VARCHAR(30) | "wifmas" |
| `uri` | `metadata_uri` | TEXT | "https://ipfs.io/ipfs/..." |
| `is_mayhem_mode` | `is_mayhem_mode` | BOOLEAN | false |
| `pool` | `pool_type` | VARCHAR(20) | "pump" |
| `price_sol` | `price_sol` | NUMERIC(30, 18) | 3.155021202521354e-8 |
| `pool_address` | `pool_address` | VARCHAR(64) | "BMyRVLmarQUvTJ7YwkH3cQsg1VgSX3fV6AKgSYNb1joR" |

---

## 📝 n8n Mapping (JavaScript)

### Für jeden Coin im Array:

```javascript
{
  // Identifikation
  token_address: $json.body.data[].mint,
  name: $json.body.data[].name,
  symbol: $json.body.data[].symbol,
  
  // Transaktions-Informationen
  signature: $json.body.data[].signature,
  trader_public_key: $json.body.data[].traderPublicKey,
  
  // Bonding Curve & Pool
  bonding_curve_key: $json.body.data[].bondingCurveKey,
  pool_address: $json.body.data[].pool_address,
  pool_type: $json.body.data[].pool,
  v_tokens_in_bonding_curve: $json.body.data[].vTokensInBondingCurve,
  v_sol_in_bonding_curve: $json.body.data[].vSolInBondingCurve,
  
  // Initial Buy
  initial_buy_sol: $json.body.data[].solAmount,
  initial_buy_tokens: $json.body.data[].initialBuy,
  
  // Preis & Market Cap
  price_sol: $json.body.data[].price_sol,
  market_cap_sol: $json.body.data[].marketCapSol,
  liquidity_sol: $json.body.data[].vSolInBondingCurve,  // Gleicher Wert wie v_sol_in_bonding_curve
  
  // Status Flags
  is_mayhem_mode: $json.body.data[].is_mayhem_mode,
  
  // Metadata
  metadata_uri: $json.body.data[].uri,
  
  // Defaults
  discovered_at: NOW(),
  open_market_cap_sol: 85000,
  blockchain_id: 1,
  is_active: true,
  final_outcome: 'PENDING',
  classification: 'UNKNOWN'
}
```

---

## 🔄 Vollständige Mapping-Liste

### Direkt vom WebSocket (15 Felder):

1. `mint` → `token_address`
2. `name` → `name`
3. `symbol` → `symbol`
4. `signature` → `signature`
5. `traderPublicKey` → `trader_public_key`
6. `bondingCurveKey` → `bonding_curve_key`
7. `pool_address` → `pool_address` (bereits berechnet im Relay)
8. `pool` → `pool_type`
9. `vTokensInBondingCurve` → `v_tokens_in_bonding_curve`
10. `vSolInBondingCurve` → `v_sol_in_bonding_curve`
11. `solAmount` → `initial_buy_sol`
12. `initialBuy` → `initial_buy_tokens`
13. `marketCapSol` → `market_cap_sol`
14. `price_sol` → `price_sol` (bereits berechnet im Relay)
15. `is_mayhem_mode` → `is_mayhem_mode`
16. `uri` → `metadata_uri`

### Berechnet im Relay (2 Felder):

17. `price_sol` → `price_sol` (berechnet aus `marketCapSol / vTokensInBondingCurve`)
18. `pool_address` → `pool_address` (gleich wie `bondingCurveKey`)

### Default-Werte (5 Felder):

19. `discovered_at` → `NOW()`
20. `open_market_cap_sol` → `85000`
21. `blockchain_id` → `1`
22. `is_active` → `TRUE`
23. `final_outcome` → `'PENDING'`

---

## ✅ Zusammenfassung

**Von deinem WebSocket-Output kannst du direkt füllen:**
- ✅ 16 Felder direkt
- ✅ 2 Felder berechnet (price_sol, pool_address)
- ✅ 5 Felder mit Defaults

**Insgesamt: 23 von 39 Feldern** (59%) direkt aus WebSocket verfügbar!

**Die restlichen Felder kommen aus:**
- API (Rug-Check): `token_decimals`, `token_supply`, `deploy_platform`, `risk_score`, `top_10_holders_pct`, `classification`
- Metadata (URI): `description`, `image_url`, `twitter_url`, `telegram_url`, `website_url`
- Berechnet: `has_socials`, `is_graduated`, `phase_id`
- Optional: `discord_url`, `status_note`, `token_created_at`


