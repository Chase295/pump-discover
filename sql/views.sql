-- ============================================================================
-- PUMP DISCOVER - Views für berechnete Werte
-- ============================================================================
-- 
-- Diese Views berechnen Werte, die nicht direkt in der Tabelle gespeichert werden.
-- USD-Umrechnungen erfolgen über Verknüpfung zu einer separaten Tabelle mit Kursen.
-- ============================================================================

-- ============================================================================
-- View: Graduation-Berechnungen
-- ============================================================================
CREATE OR REPLACE VIEW discovered_coins_graduation AS
SELECT 
    token_address,
    name,
    symbol,
    market_cap_sol,
    open_market_cap_sol,
    -- Berechnete Felder
    (open_market_cap_sol - market_cap_sol) AS distance_to_graduation_sol,
    ROUND((market_cap_sol / open_market_cap_sol * 100)::NUMERIC, 2) AS graduation_progress_pct,
    is_graduated,
    discovered_at
FROM discovered_coins
WHERE is_active = TRUE;

-- ============================================================================
-- View: Mit USD-Werten (über Kurs-Tabelle)
-- ============================================================================
-- ANPASSUNG ERFORDERLICH: Ersetze 'exchange_rates' mit deiner tatsächlichen Kurs-Tabelle
-- ANPASSUNG ERFORDERLICH: Ersetze 'sol_price_usd' mit deinem tatsächlichen Kurs-Feld
-- 
-- Beispiel-Struktur:
-- CREATE OR REPLACE VIEW discovered_coins_with_usd AS
-- SELECT 
--     dc.*,
--     er.sol_price_usd,
--     (dc.market_cap_sol * er.sol_price_usd) AS market_cap_usd,
--     (dc.liquidity_sol * er.sol_price_usd) AS liquidity_usd,
--     (dc.initial_buy_sol * er.sol_price_usd) AS initial_buy_usd,
--     (dc.price_sol * er.sol_price_usd) AS price_usd
-- FROM discovered_coins dc
-- CROSS JOIN LATERAL (
--     SELECT sol_price_usd 
--     FROM exchange_rates 
--     WHERE currency = 'SOL' 
--     ORDER BY timestamp DESC 
--     LIMIT 1
-- ) er
-- WHERE dc.is_active = TRUE;
-- ============================================================================

-- ============================================================================
-- View: Aktive Coins mit allen Berechnungen
-- ============================================================================
CREATE OR REPLACE VIEW discovered_coins_active AS
SELECT 
    dc.*,
    -- Graduation-Berechnungen
    (dc.open_market_cap_sol - dc.market_cap_sol) AS distance_to_graduation_sol,
    ROUND((dc.market_cap_sol / dc.open_market_cap_sol * 100)::NUMERIC, 2) AS graduation_progress_pct
FROM discovered_coins dc
WHERE dc.is_active = TRUE;

-- ============================================================================
-- View: Coins nahe der Graduierung (für Filterung)
-- ============================================================================
CREATE OR REPLACE VIEW discovered_coins_near_graduation AS
SELECT 
    token_address,
    name,
    symbol,
    market_cap_sol,
    open_market_cap_sol,
    (open_market_cap_sol - market_cap_sol) AS distance_to_graduation_sol,
    ROUND((market_cap_sol / open_market_cap_sol * 100)::NUMERIC, 2) AS graduation_progress_pct,
    discovered_at,
    trader_public_key,
    initial_buy_sol
FROM discovered_coins
WHERE is_active = TRUE
  AND is_graduated = FALSE
  AND market_cap_sol > 0
ORDER BY graduation_progress_pct DESC;

