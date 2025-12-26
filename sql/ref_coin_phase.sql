CREATE TABLE ref_coin_phases (
    id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    interval_seconds INT NOT NULL,
    
    -- Das Zeitfenster (Start und Ende)
    min_age_minutes INT NOT NULL,
    max_age_minutes INT NOT NULL
);

-- Initiale Daten
INSERT INTO ref_coin_phases (id, name, interval_seconds, min_age_minutes, max_age_minutes) VALUES
(1, 'Baby Zone',      5,    0,   10),   -- Von 0 bis 10 Min
(2, 'Survival Zone', 30,   10,   60),   -- Von 10 bis 60 Min
(3, 'Mature Zone',   60,   60, 1440),   -- Von 1 Std bis 24 Std
(99, 'Finished',      0, 1440, 999999); -- Ab 24 Std bis Unendlich
(100, 'Graduated',      0, 1440, 999999)