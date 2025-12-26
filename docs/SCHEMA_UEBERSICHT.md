# 📊 Pump Discover - Datenbankschema Übersicht

## 🎯 Übersicht

Dieses Dokument beschreibt das vollständige Datenbankschema für das Pump Discover Projekt. Das Schema speichert alle Informationen über neu erstellte Pump.fun Tokens, die über den WebSocket empfangen, in n8n gefiltert und dann in der Datenbank gespeichert werden.

**Datenfluss:** `Pump.fun WebSocket → Python Relay → n8n (Filterung) → Datenbank`

---

## 📋 Tabellenstruktur: `discovered_coins`

### 1. Identifikation (4 Felder)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `token_address` | VARCHAR(64) | Mint-Adresse (PRIMARY KEY) | WebSocket: `mint` |
| `blockchain_id` | INT | Blockchain ID (1 = Solana) | Default: 1 |
| `symbol` | VARCHAR(30) | Token-Symbol | WebSocket: `symbol` |
| `name` | VARCHAR(255) | Token-Name | WebSocket: `name` |

### 2. Transaktions-Informationen (2 Felder)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `signature` | VARCHAR(88) | Transaktions-Signatur | WebSocket: `signature` |
| `trader_public_key` | VARCHAR(44) | Creator/Trader Public Key | WebSocket: `traderPublicKey` |

**Wichtig für:** Risiko-Analyse, Creator-Tracking, Verifizierung

### 3. Bonding Curve & Pool (5 Felder)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `bonding_curve_key` | VARCHAR(44) | Bonding Curve Adresse | WebSocket: `bondingCurveKey` |
| `pool_address` | VARCHAR(64) | Pool-Adresse | WebSocket: `pool` |
| `pool_type` | VARCHAR(20) | Pool-Typ (meist "pump") | WebSocket: `pool` |
| `v_tokens_in_bonding_curve` | NUMERIC(30,6) | Virtuelle Tokens | WebSocket: `vTokensInBondingCurve` |
| `v_sol_in_bonding_curve` | NUMERIC(20,6) | Virtuelles SOL | WebSocket: `vSolInBondingCurve` |

**Wichtig für:** Tokenomics-Analyse, Liquiditäts-Tracking

### 4. Initial Buy (2 Felder)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `initial_buy_sol` | NUMERIC(20,6) | SOL Betrag beim initialen Buy | WebSocket: `solAmount` |
| `initial_buy_tokens` | NUMERIC(30,6) | Anzahl Tokens beim initialen Buy | WebSocket: `initialBuy` |

**Wichtig für:** Creator-Commitment-Analyse, Risiko-Bewertung

### 5. Zeitstempel (2 Felder)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `discovered_at` | TIMESTAMP | Wann wurde der Coin entdeckt | Auto: NOW() |
| `token_created_at` | TIMESTAMP | Wann wurde der Token erstellt | Aus Signature/Timestamp |

**Wichtig für:** Alters-Analyse, Timing-Analyse

### 6. Preis & Market Cap (nur SOL, USD über separate Kurs-Tabelle)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `price_sol` | NUMERIC(30,18) | Preis in SOL | Berechnet aus `marketCapSol` |
| `market_cap_sol` | NUMERIC(20,2) | Market Cap in SOL | WebSocket: `marketCapSol` |
| `liquidity_sol` | NUMERIC(20,6) | Liquidität in SOL | WebSocket: `vSolInBondingCurve` |

**Hinweis:** USD-Werte werden über Views mit Verknüpfung zu einer separaten Kurs-Tabelle berechnet.

**Wichtig für:** Filterung, Preis-Tracking

### 7. Graduation / Open Market Cap (1 Feld, Berechnungen über Views)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `open_market_cap_sol` | NUMERIC(20,2) | Fester Wert für Graduierung (~85,000 SOL) | Default: 85000 |

**Berechnungen über Views:**
- `distance_to_graduation_sol = open_market_cap_sol - market_cap_sol`
- `graduation_progress_pct = (market_cap_sol / open_market_cap_sol) * 100`

**Wichtig für:** Graduation-Tracking, Filterung nahe der Graduierung

### 8. Status Flags (3 Felder)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `is_mayhem_mode` | BOOLEAN | Spezieller "Mayhem Mode" Flag | WebSocket: `is_mayhem_mode` |
| `is_graduated` | BOOLEAN | Ob der Token bereits graduiert ist | n8n/Update |
| `is_active` | BOOLEAN | Ob der Token noch aktiv ist | Default: TRUE |

### 9. Risiko & Analyse (3 Felder)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `risk_score` | INT | Risiko-Score (0-100) | n8n/KI-Analyse |
| `top_10_holders_pct` | NUMERIC(5,2) | Prozentualer Anteil der Top-10-Holder | n8n/On-Chain-Analyse |
| `has_socials` | BOOLEAN | Ob Social Media vorhanden ist | Berechnet in n8n |

**Wichtig für:** Risiko-Filterung, KI-Auswertung

### 10. Metadata & Social Media (7 Felder)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `metadata_uri` | TEXT | URI zur Metadata (IPFS/RapidLaunch) | WebSocket: `uri` |
| `description` | TEXT | Token-Beschreibung | Metadata: `description` |
| `image_url` | TEXT | Bild-URL | Metadata: `image` |
| `twitter_url` | TEXT | Twitter/X URL | Metadata: `twitter` |
| `telegram_url` | TEXT | Telegram URL | Metadata: `telegram` |
| `website_url` | TEXT | Website URL | Metadata: `website` |
| `discord_url` | TEXT | Discord URL | Metadata: `discord` |

**Hinweis:** Metadata wird in n8n von der `metadata_uri` abgerufen und geparst.

### 11. Management & Klassifizierung (3 Felder)
| Feld | Typ | Beschreibung | Quelle |
|------|-----|--------------|--------|
| `final_outcome` | VARCHAR(20) | Ergebnis: PENDING, GRADUATED, RUG, etc. | n8n/Update |
| `classification` | VARCHAR(50) | Klassifizierung | n8n/KI-Analyse |
| `status_note` | VARCHAR(255) | Notiz zum Status | n8n/Manuell |

---

## 🔍 Indexe

### Performance-Indexe:
- `idx_dc_active` - Für aktive Tokens
- `idx_dc_graduated` - Für graduierte Tokens
- `idx_dc_discovered` - Sortierung nach Entdeckungszeit
- `idx_dc_created_at` - Sortierung nach Erstellungszeit

### Analyse-Indexe:
- `idx_dc_trader` - Für Creator-Analyse
- `idx_dc_signature` - Für Transaktions-Tracking
- `idx_dc_initial_buy` - Für Commitment-Analyse
- `idx_dc_market_cap_sol` - Für Market Cap Filterung
- `idx_dc_graduation_progress` - Für Graduation-Tracking
- `idx_dc_risk_score` - Für Risiko-Filterung
- `idx_dc_classification` - Für Klassifizierung

---

## 📊 Datenquellen-Mapping

### Direkt vom WebSocket (15 Felder):
```
mint                    → token_address
name                    → name
symbol                  → symbol
signature               → signature
traderPublicKey         → trader_public_key
bondingCurveKey         → bonding_curve_key
pool                    → pool_type / pool_address
vTokensInBondingCurve   → v_tokens_in_bonding_curve
vSolInBondingCurve      → v_sol_in_bonding_curve
solAmount               → initial_buy_sol
initialBuy              → initial_buy_tokens
marketCapSol            → market_cap_sol
is_mayhem_mode          → is_mayhem_mode
uri                     → metadata_uri
```

### Aus Metadata URI (in n8n extrahiert):
```
metadata.description    → description
metadata.image          → image_url
metadata.twitter        → twitter_url
metadata.telegram       → telegram_url
metadata.website        → website_url
metadata.discord        → discord_url
```

### Berechnet in n8n:
```
marketCapSol            → price_sol (berechnet)
```

### Berechnet über Views (nicht in Tabelle gespeichert):
```
open_market_cap_sol - market_cap_sol → distance_to_graduation_sol
(market_cap_sol / open_market_cap_sol) * 100 → graduation_progress_pct
```

### USD-Werte über Views mit Kurs-Tabelle:
```
market_cap_sol * sol_price_usd → market_cap_usd
liquidity_sol * sol_price_usd → liquidity_usd
initial_buy_sol * sol_price_usd → initial_buy_usd
price_sol * sol_price_usd → price_usd
```

---

## 🎯 Verwendung in n8n

### 1. Webhook empfängt Daten vom Python Relay:
```json
{
  "mint": "...",
  "name": "...",
  "symbol": "...",
  "signature": "...",
  "traderPublicKey": "...",
  "marketCapSol": 29.5,
  "uri": "https://ipfs.io/ipfs/...",
  ...
}
```

### 2. Metadata abrufen:
- HTTP Request Node: `GET {uri}`
- Parse JSON Response
- Extrahiere: description, image, twitter, telegram, website, discord

### 3. Berechnungen:
- `price_sol` = berechnet aus marketCapSol
- `liquidity_sol` = direkt vom WebSocket (vSolInBondingCurve)

**Hinweis:** Graduation-Berechnungen und USD-Werte werden über Views berechnet, nicht in n8n.

### 4. Filterung:
- Market Cap > 30k USD?
- Graduation Progress > 50%?
- Initial Buy > 1 SOL?
- Has Socials?

### 5. Datenbank-Insert:
- PostgreSQL Node
- INSERT INTO discovered_coins (...)
- Alle Felder mappen

---

## 📈 Gesamtübersicht

**Gesamt: 36 Felder in der Tabelle**
- ✅ 15 Felder direkt vom WebSocket
- ✅ 7 Felder aus Metadata (in n8n extrahiert)
- ✅ 1 Feld für Graduation (open_market_cap_sol)
- ✅ 13 Felder für Management/Analyse

**Berechnete Werte über Views:**
- Graduation-Berechnungen (distance, progress)
- USD-Umrechnungen (über separate Kurs-Tabelle)

**Indexe: 11 Indexe** für optimale Performance

---

## 🔍 Views für berechnete Werte

### `discovered_coins_graduation`
Zeigt alle aktiven Coins mit Graduation-Berechnungen:
- `distance_to_graduation_sol`
- `graduation_progress_pct`

### `discovered_coins_active`
Zeigt alle aktiven Coins mit allen Berechnungen.

### `discovered_coins_near_graduation`
Zeigt Coins nahe der Graduierung, sortiert nach Progress.

### `discovered_coins_with_usd` (Beispiel)
Zeigt alle Coins mit USD-Werten über Kurs-Tabelle.
**Hinweis:** Muss an deine Kurs-Tabelle angepasst werden.

---

## 🔄 Wartung & Updates

### Regelmäßige Updates:
- `is_graduated` - Update wenn Token graduiert
- `final_outcome` - Update basierend auf Ergebnis
- `risk_score` - Update durch KI-Analyse
- `classification` - Update durch KI-Analyse

### Berechnete Felder:
- `distance_to_graduation_sol` - Kann bei Updates neu berechnet werden
- `graduation_progress_pct` - Kann bei Updates neu berechnet werden

