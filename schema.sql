-- =====================================================================
-- SQLite Relational Schema: Polymer Property Prediction Platform
-- =====================================================================

PRAGMA foreign_keys = ON;

-- 1. Core Molecular Log Table
CREATE TABLE IF NOT EXISTS Molecules (
    molecule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    smiles_string TEXT NOT NULL,
    canonical_smiles TEXT NOT NULL UNIQUE,
    sa_score REAL,                      -- Synthetic Accessibility Score (1.0 - 10.0)
    is_valid BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Property Predictions Table (1-to-Many Relationship with Molecules)
CREATE TABLE IF NOT EXISTS PropertyPredictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    molecule_id INTEGER NOT NULL,
    property_name VARCHAR(50) NOT NULL, -- e.g., 'Glass Transition Temp (Tg)', 'Density'
    predicted_value REAL NOT NULL,
    unit VARCHAR(20) NOT NULL,          -- e.g., '°C', 'g/cm³'
    model_version VARCHAR(30) DEFAULT 'v1.0-oracle',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (molecule_id) REFERENCES Molecules(molecule_id) ON DELETE CASCADE
);

-- 3. Validation & Exception Logs Table
CREATE TABLE IF NOT EXISTS ValidationLogs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    smiles_input TEXT NOT NULL,
    is_valid BOOLEAN NOT NULL,
    error_stage VARCHAR(50),           -- 'Syntax Check', 'Sanitization', 'Valence'
    error_message TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Fast Querying & Search Operations
CREATE INDEX IF NOT EXISTS idx_molecules_canonical ON Molecules(canonical_smiles);
CREATE INDEX IF NOT EXISTS idx_predictions_molecule ON PropertyPredictions(molecule_id);
