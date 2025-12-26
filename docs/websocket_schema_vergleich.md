# WebSocket Daten vs. SQL Schema Vergleich

## 📡 Vom Pump.fun WebSocket erhaltene Felder (15 Felder):

### ✅ Bereits im Schema vorhanden:
1. **mint** → `token_address` ✓
2. **name** → `name` ✓
3. **symbol** → `symbol` ✓
4. **marketCapSol** → kann zu `price_sol` und `market_cap_usd` konvertiert werden ✓
5. **vSolInBondingCurve** → kann zu `liquidity_usd` konvertiert werden ✓

### ❌ FEHLT im Schema (direkt vom WebSocket):

#### 1. Transaktions-Informationen:
- **signature** - Transaktions-Signatur (wichtig für Verifizierung)
- **txType** - Typ der Transaktion ("create", "buy", "sell", etc.)
- **traderPublicKey** - Public Key des Creators/Traders (wichtig für Risiko-Analyse)

#### 2. Bonding Curve Details:
- **bondingCurveKey** - Adresse der Bonding Curve (könnte `pool_address` sein?)
- **vTokensInBondingCurve** - Virtuelle Tokens in der Bonding Curve
- **vSolInBondingCurve** - Virtuelles SOL in der Bonding Curve (bereits indirekt vorhanden)

#### 3. Initial Buy Information:
- **initialBuy** - Anzahl Tokens beim initialen Buy
- **solAmount** - SOL Betrag beim initialen Buy

#### 4. Metadata & Status:
- **uri** - URI zur Metadata (könnte `image_url` und `description` enthalten - muss geparst werden)
- **is_mayhem_mode** - Boolean Flag für "Mayhem Mode"
- **pool** - Pool-Typ (z.B. "pump")

## 🔍 Zusätzliche Daten die aus der URI kommen könnten:

Die `uri` zeigt auf JSON-Metadata (IPFS oder RapidLaunch). Diese könnte enthalten:
- `image` → `image_url`
- `description` → `description`
- `twitter`, `telegram`, `website`, `discord` → entsprechende URL-Felder
- Weitere Metadaten

## 📊 Empfohlene Schema-Erweiterungen:

### Direkt vom WebSocket speichern:
```sql
-- Transaktions-Info
signature VARCHAR(88) NOT NULL,  -- Solana Signature
tx_type VARCHAR(20),               -- "create", "buy", "sell"
trader_public_key VARCHAR(44),    -- Creator/Trader Public Key

-- Bonding Curve
bonding_curve_key VARCHAR(44),    -- Bonding Curve Adresse
v_tokens_in_bonding_curve NUMERIC(30, 6),
v_sol_in_bonding_curve NUMERIC(20, 6),

-- Initial Buy
initial_buy_tokens NUMERIC(30, 6),
initial_buy_sol NUMERIC(20, 6),

-- Status Flags
is_mayhem_mode BOOLEAN DEFAULT FALSE,
pool_type VARCHAR(20),             -- "pump" oder andere

-- Metadata URI (für spätere Abfrage)
metadata_uri TEXT,
```

### Aus Metadata URI extrahieren (via n8n):
- `image_url` (aus metadata.image)
- `description` (aus metadata.description)
- `twitter_url` (aus metadata.twitter)
- `telegram_url` (aus metadata.telegram)
- `website_url` (aus metadata.website)
- `discord_url` (aus metadata.discord)

## 🎯 Priorität für KI-Auswertung:

### Hoch:
- **trader_public_key** - Für Creator-Analyse (Rug-Pull-Risiko)
- **signature** - Für Transaktions-Verifizierung
- **initial_buy_sol** - Initial Investment Größe
- **is_mayhem_mode** - Spezieller Modus

### Mittel:
- **bonding_curve_key** - Für Liquiditäts-Tracking
- **v_tokens_in_bonding_curve** - Für Tokenomics-Analyse
- **tx_type** - Für Transaktions-Historie

### Niedrig:
- **pool_type** - Meistens "pump"
- **metadata_uri** - Wird in n8n geparst

