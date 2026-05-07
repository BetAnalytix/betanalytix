-- BetAnalytix — table de sauvegarde des prédictions
-- Exécuter dans Supabase > SQL Editor

CREATE TABLE IF NOT EXISTS predictions (
    id               BIGSERIAL PRIMARY KEY,
    date             DATE             NOT NULL,
    sport            TEXT             NOT NULL,
    home_team        TEXT             NOT NULL,
    away_team        TEXT             NOT NULL,
    bet              TEXT             NOT NULL CHECK (bet IN ('home', 'away')),
    odds             NUMERIC(5, 2)    NOT NULL,
    model_prob       NUMERIC(6, 4)    NOT NULL,
    edge             NUMERIC(6, 4)    NOT NULL,
    confidence_score NUMERIC(5, 1)    NOT NULL,
    kelly_stake      NUMERIC(7, 2)    NOT NULL,
    status           TEXT             NOT NULL DEFAULT 'pending'
                         CHECK (status IN ('pending', 'won', 'lost', 'void')),
    created_at       TIMESTAMPTZ      DEFAULT NOW()
);

-- Index pour requêtes fréquentes par date et sport
CREATE INDEX IF NOT EXISTS idx_predictions_date  ON predictions (date DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_sport ON predictions (sport);
CREATE INDEX IF NOT EXISTS idx_predictions_status ON predictions (status);

-- Row Level Security : autoriser l'anon key à insérer et lire
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_insert"
    ON predictions FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "anon_select"
    ON predictions FOR SELECT
    TO anon
    USING (true);
