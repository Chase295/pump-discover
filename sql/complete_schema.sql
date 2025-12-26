-- ============================================================================
-- PUMP DISCOVER - VOLLSTÄNDIGES DATENBANKSCHEMA
-- ============================================================================
-- 
-- Dieses Schema erstellt alle 3 Tabellen für das Pump Discover Projekt:
-- 1. discovered_coins - Haupttabelle für entdeckte Tokens
-- 2. coin_streams - Tabelle für kontinuierliches Metriken-Tracking
-- 3. ref_coin_phases - Referenztabelle für Coin-Phasen
--
-- Datenfluss: Pump.fun WebSocket → Python Relay → n8n (Filterung) → Datenbank
-- ============================================================================

-- ============================================================================
-- 1. DISCOVERED_COINS - Haupttabelle für entdeckte Tokens
-- ============================================================================

DROP TABLE IF EXISTS discovered_coins CASCADE;

CREATE TABLE discovered_coins (
    -- ============================================================================
    -- 1. IDENTIFIKATION
    -- ============================================================================
    token_address VARCHAR(64) NOT NULL,           -- Mint-Adresse (PRIMARY KEY)
    blockchain_id INT NOT NULL DEFAULT 1,         -- Blockchain ID (1 = Solana)
    symbol VARCHAR(30),                           -- Token-Symbol
    name VARCHAR(255),                            -- Token-Name
    token_decimals INT,                           -- Token Decimals (vom API: token.decimals)
    token_supply NUMERIC(30, 6),                  -- Token Supply (vom API: token.supply)
    deploy_platform VARCHAR(50),                 -- Deployment Platform (vom API: deployPlatform)
    
    PRIMARY KEY (token_address),
    
    -- ============================================================================
    -- 2. TRANSAKTIONS-INFORMATIONEN
    -- ============================================================================
    signature VARCHAR(88),                        -- Transaktions-Signatur (für Verifizierung)
    trader_public_key VARCHAR(44),                -- Creator/Trader Public Key (für Risiko-Analyse)
    
    -- ============================================================================
    -- 3. BONDING CURVE & POOL INFORMATIONEN
    -- ============================================================================
    bonding_curve_key VARCHAR(44),               -- Bonding Curve Adresse
    pool_address VARCHAR(64),                     -- Pool-Adresse (falls unterschiedlich)
    pool_type VARCHAR(20) DEFAULT 'pump',         -- Pool-Typ (meist "pump")
    v_tokens_in_bonding_curve NUMERIC(30, 6),    -- Virtuelle Tokens in Bonding Curve
    v_sol_in_bonding_curve NUMERIC(20, 6),       -- Virtuelles SOL in Bonding Curve
    
    -- ============================================================================
    -- 4. INITIAL BUY INFORMATIONEN
    -- ============================================================================
    initial_buy_sol NUMERIC(20, 6),               -- SOL Betrag beim initialen Buy
    initial_buy_tokens NUMERIC(30, 6),           -- Anzahl Tokens beim initialen Buy
    
    -- ============================================================================
    -- 5. ZEITSTEMPEL
    -- ============================================================================
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- Wann wurde der Coin entdeckt
    token_created_at TIMESTAMP WITH TIME ZONE,             -- Wann wurde der Token erstellt
    
    -- ============================================================================
    -- 6. PREIS & MARKET CAP (nur SOL, USD über separate Tabelle mit Kursen)
    -- ============================================================================
    price_sol NUMERIC(30, 18),                    -- Preis in SOL
    market_cap_sol NUMERIC(20, 2),                -- Market Cap in SOL (vom WebSocket: marketCapSol)
    liquidity_sol NUMERIC(20, 6),                 -- Liquidität in SOL (vom WebSocket: vSolInBondingCurve)
    
    -- ============================================================================
    -- 7. GRADUATION (Open Market Cap)
    -- ============================================================================
    open_market_cap_sol NUMERIC(20, 2) DEFAULT 85000,  -- Fester Wert für Graduierung (~85,000 SOL)
                                                        -- Berechnungen (distance, progress) über Views
    phase_id INT,                                       -- Phase ID (vom WebSocket: phaseId)
    
    -- ============================================================================
    -- 8. STATUS FLAGS
    -- ============================================================================
    is_mayhem_mode BOOLEAN DEFAULT FALSE,         -- Spezieller "Mayhem Mode" Flag
    is_graduated BOOLEAN DEFAULT FALSE,           -- Ob der Token bereits graduiert ist
    is_active BOOLEAN DEFAULT TRUE,               -- Ob der Token noch aktiv ist
    
    -- ============================================================================
    -- 9. RISIKO & ANALYSE
    -- ============================================================================
    risk_score INT,                               -- Risiko-Score (0-100)
    top_10_holders_pct NUMERIC(5, 2),             -- Prozentualer Anteil der Top-10-Holder
    has_socials BOOLEAN DEFAULT FALSE,           -- Ob Social Media vorhanden ist
    social_count INT DEFAULT 0,                   -- Anzahl Social-Links (0-4): Twitter + Telegram + Website + Discord
    metadata_is_mutable BOOLEAN,                  -- Kann Dev Metadata nachträglich ändern? (aus RugCheck API)
    mint_authority_enabled BOOLEAN,                -- Kann Dev neue Tokens drucken? (aus RugCheck API)
    image_hash VARCHAR(64),                       -- pHash des Bildes (für Lazy Scam Detection)
    
    -- ============================================================================
    -- 10. METADATA & SOCIAL MEDIA
    -- ============================================================================
    metadata_uri TEXT,                             -- URI zur Metadata (IPFS/RapidLaunch)
    description TEXT,                              -- Token-Beschreibung (aus Metadata)
    image_url TEXT,                                -- Bild-URL (aus Metadata)
    twitter_url TEXT,                              -- Twitter/X URL (aus Metadata)
    telegram_url TEXT,                             -- Telegram URL (aus Metadata)
    website_url TEXT,                              -- Website URL (aus Metadata)
    discord_url TEXT,                              -- Discord URL (aus Metadata)
    
    -- ============================================================================
    -- 11. MANAGEMENT & KLASSIFIZIERUNG
    -- ============================================================================
    final_outcome VARCHAR(20) DEFAULT 'PENDING', -- Ergebnis: PENDING, GRADUATED, RUG, etc.
    classification VARCHAR(50) DEFAULT 'UNKNOWN', -- Klassifizierung
    status_note VARCHAR(255)                      -- Notiz zum Status
);

-- ============================================================================
-- INDEXE für discovered_coins
-- ============================================================================

-- Basis-Indexe
CREATE INDEX idx_dc_active ON discovered_coins(is_active);
CREATE INDEX idx_dc_graduated ON discovered_coins(is_graduated);
CREATE INDEX idx_dc_discovered ON discovered_coins(discovered_at DESC);
CREATE INDEX idx_dc_created_at ON discovered_coins(token_created_at);

-- Transaktions-Indexe
CREATE INDEX idx_dc_trader ON discovered_coins(trader_public_key);
CREATE INDEX idx_dc_signature ON discovered_coins(signature);

-- Initial Buy Index (für Commitment-Analyse)
CREATE INDEX idx_dc_initial_buy ON discovered_coins(initial_buy_sol DESC);

-- Market Cap Indexe
CREATE INDEX idx_dc_market_cap_sol ON discovered_coins(market_cap_sol DESC);

-- Phase-Index
CREATE INDEX idx_dc_phase_id ON discovered_coins(phase_id);

-- Token-Indexe
CREATE INDEX idx_dc_deploy_platform ON discovered_coins(deploy_platform);

-- Risiko-Indexe
CREATE INDEX idx_dc_risk_score ON discovered_coins(risk_score);
CREATE INDEX idx_dc_classification ON discovered_coins(classification);
CREATE INDEX idx_dc_social_count ON discovered_coins(social_count);
CREATE INDEX idx_dc_metadata_mutable ON discovered_coins(metadata_is_mutable);
CREATE INDEX idx_dc_mint_authority ON discovered_coins(mint_authority_enabled);
CREATE INDEX idx_dc_image_hash ON discovered_coins(image_hash);

-- ============================================================================
-- KOMMENTARE für discovered_coins
-- ============================================================================

COMMENT ON TABLE discovered_coins IS 'Speichert alle entdeckten Pump.fun Tokens mit vollständigen Metadaten';
COMMENT ON COLUMN discovered_coins.token_address IS 'Eindeutige Token-Adresse (Mint) - PRIMARY KEY';
COMMENT ON COLUMN discovered_coins.trader_public_key IS 'Public Key des Creators - wichtig für Risiko-Analyse';
COMMENT ON COLUMN discovered_coins.bonding_curve_key IS 'Adresse der Bonding Curve';
COMMENT ON COLUMN discovered_coins.initial_buy_sol IS 'SOL Betrag beim initialen Buy - Indikator für Creator-Commitment';
COMMENT ON COLUMN discovered_coins.market_cap_sol IS 'Market Cap in SOL (direkt vom WebSocket: marketCapSol)';
COMMENT ON COLUMN discovered_coins.liquidity_sol IS 'Liquidität in SOL (direkt vom WebSocket: vSolInBondingCurve)';
COMMENT ON COLUMN discovered_coins.open_market_cap_sol IS 'Fester Wert für Graduierung (~85,000 SOL). Berechnungen über Views.';
COMMENT ON COLUMN discovered_coins.phase_id IS 'Phase ID vom WebSocket (phaseId)';
COMMENT ON COLUMN discovered_coins.token_decimals IS 'Token Decimals (vom API: token.decimals)';
COMMENT ON COLUMN discovered_coins.token_supply IS 'Token Supply (vom API: token.supply)';
COMMENT ON COLUMN discovered_coins.deploy_platform IS 'Deployment Platform (vom API: deployPlatform, z.B. "rapidlaunch")';
COMMENT ON COLUMN discovered_coins.is_mayhem_mode IS 'Spezieller Modus bei Pump.fun';
COMMENT ON COLUMN discovered_coins.metadata_uri IS 'URI zur Metadata (wird in n8n geparst)';
COMMENT ON COLUMN discovered_coins.social_count IS 'Anzahl Social-Links (0-4): Twitter + Telegram + Website + Discord - für KI-Analyse';
COMMENT ON COLUMN discovered_coins.metadata_is_mutable IS 'Kann Dev Metadata nachträglich ändern? (aus RugCheck API: metadata.isMutable) - Soft-Rug-Indikator';
COMMENT ON COLUMN discovered_coins.mint_authority_enabled IS 'Kann Dev neue Tokens drucken? (aus RugCheck API: mintAuthority.enabled) - Hartes Ausschlusskriterium';
COMMENT ON COLUMN discovered_coins.image_hash IS 'pHash des Bildes (64 Zeichen) - für Lazy Scam Detection: Erkennung von Coins mit identischem Bild';

-- ============================================================================
-- 2. COIN_STREAMS - Tabelle für kontinuierliche Metriken-Tracking
-- ============================================================================

DROP TABLE IF EXISTS coin_streams CASCADE;

CREATE TABLE coin_streams (
    id BIGSERIAL NOT NULL,
    token_address VARCHAR(64) NOT NULL,
    current_phase_id INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    is_graduated BOOLEAN DEFAULT false,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT coin_streams_pkey PRIMARY KEY (id),
    CONSTRAINT unique_active_stream UNIQUE (token_address)
);

-- ============================================================================
-- INDEXE für coin_streams
-- ============================================================================

CREATE INDEX idx_coin_streams_token_address ON coin_streams(token_address);
CREATE INDEX idx_coin_streams_phase_id ON coin_streams(current_phase_id);
CREATE INDEX idx_coin_streams_active ON coin_streams(is_active);
CREATE INDEX idx_coin_streams_graduated ON coin_streams(is_graduated);

-- ============================================================================
-- KOMMENTARE für coin_streams
-- ============================================================================

COMMENT ON TABLE coin_streams IS 'Speichert aktive Coin-Streams für kontinuierliches Metriken-Tracking';
COMMENT ON COLUMN coin_streams.id IS 'Eindeutige ID (BIGSERIAL)';
COMMENT ON COLUMN coin_streams.token_address IS 'Token-Adresse (Referenz zu discovered_coins)';
COMMENT ON COLUMN coin_streams.current_phase_id IS 'Aktuelle Phase ID (Referenz zu ref_coin_phases)';
COMMENT ON COLUMN coin_streams.is_active IS 'Ob der Stream noch aktiv ist';
COMMENT ON COLUMN coin_streams.is_graduated IS 'Ob der Token bereits graduiert ist';
COMMENT ON COLUMN coin_streams.started_at IS 'Wann der Stream gestartet wurde';

-- ============================================================================
-- 3. REF_COIN_PHASES - Referenztabelle für Coin-Phasen
-- ============================================================================

DROP TABLE IF EXISTS ref_coin_phases CASCADE;

CREATE TABLE ref_coin_phases (
    id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    interval_seconds INT NOT NULL,
    min_age_minutes INT NOT NULL,
    max_age_minutes INT NOT NULL
);

-- ============================================================================
-- INITIALE DATEN für ref_coin_phases
-- ============================================================================

INSERT INTO ref_coin_phases (id, name, interval_seconds, min_age_minutes, max_age_minutes) VALUES
(1, 'Baby Zone', 5, 0, 10),           -- Von 0 bis 10 Min
(2, 'Survival Zone', 30, 10, 60),     -- Von 10 bis 60 Min
(3, 'Mature Zone', 60, 60, 1440),     -- Von 1 Std bis 24 Std
(99, 'Finished', 0, 1440, 999999),    -- Ab 24 Std bis Unendlich
(100, 'Graduated', 0, 1440, 999999);  -- Graduierte Tokens

-- ============================================================================
-- INDEXE für ref_coin_phases
-- ============================================================================

CREATE INDEX idx_ref_coin_phases_id ON ref_coin_phases(id);

-- ============================================================================
-- KOMMENTARE für ref_coin_phases
-- ============================================================================

COMMENT ON TABLE ref_coin_phases IS 'Referenztabelle für Coin-Phasen (Baby Zone, Survival Zone, etc.)';
COMMENT ON COLUMN ref_coin_phases.id IS 'Eindeutige Phase ID';
COMMENT ON COLUMN ref_coin_phases.name IS 'Name der Phase (z.B. "Baby Zone", "Survival Zone")';
COMMENT ON COLUMN ref_coin_phases.interval_seconds IS 'Intervall in Sekunden für Metriken-Updates in dieser Phase';
COMMENT ON COLUMN ref_coin_phases.min_age_minutes IS 'Minimales Alter in Minuten für diese Phase';
COMMENT ON COLUMN ref_coin_phases.max_age_minutes IS 'Maximales Alter in Minuten für diese Phase';

-- ============================================================================
-- FERTIG!
-- ============================================================================
-- 
-- Alle 3 Tabellen wurden erfolgreich erstellt:
-- ✅ discovered_coins - Haupttabelle für entdeckte Tokens
-- ✅ coin_streams - Tabelle für kontinuierliches Metriken-Tracking
-- ✅ ref_coin_phases - Referenztabelle für Coin-Phasen
--
-- ============================================================================

