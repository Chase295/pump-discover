-- ============================================================================
-- PUMP DISCOVER - Datenbankschema für entdeckte Pump.fun Tokens
-- ============================================================================
-- 
-- Dieses Schema speichert alle Informationen über neu erstellte Tokens
-- von Pump.fun, die über den WebSocket empfangen und in n8n gefiltert werden.
--
-- Datenfluss: Pump.fun WebSocket → Python Relay → n8n (Filterung) → Datenbank
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
-- INDEXE für Performance
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
-- KOMMENTARE für Dokumentation
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
