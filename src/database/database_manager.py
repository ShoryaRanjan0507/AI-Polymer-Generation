import sqlite3
import os
from typing import Optional, List, Dict, Any, Tuple

class DatabaseManager:
    """
    Manages SQLite database connections, schema initialization, 
    and thread-safe CRUD operations for polymer structures and predictions.
    """
    def __init__(self, db_path: str = "polymer_data.db"):
        self.db_path = db_path
        self._shared_conn = None
        if self.db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:")
            self._shared_conn.execute("PRAGMA foreign_keys = ON;")
            self._shared_conn.row_factory = sqlite3.Row
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            return self._shared_conn
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        return conn


    def _init_db(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        schema_path = os.path.join(root_dir, "schema.sql")
        if not os.path.exists(schema_path):
            schema_path = "schema.sql"
            
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn = self.get_connection()
        try:
            conn.executescript(schema_sql)
            conn.commit()
        finally:
            if self.db_path != ":memory:":
                conn.close()


    def insert_molecule(self, smiles_string: str, canonical_smiles: str, sa_score: Optional[float] = None) -> int:
        """
        Inserts a molecule into the DB. If canonical_smiles exists, returns existing molecule_id.
        """
        query = """
        INSERT INTO Molecules (smiles_string, canonical_smiles, sa_score)
        VALUES (?, ?, ?)
        ON CONFLICT(canonical_smiles) DO UPDATE SET
            smiles_string = excluded.smiles_string
        RETURNING molecule_id;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, (smiles_string, canonical_smiles, sa_score))
                row = cursor.fetchone()
                conn.commit()
                if row:
                    return row["molecule_id"]
            except sqlite3.Error:
                # Handle SQLite fallback for ON CONFLICT DO UPDATE RETURNING
                cursor.execute("SELECT molecule_id FROM Molecules WHERE canonical_smiles = ?", (canonical_smiles,))
                existing = cursor.fetchone()
                if existing:
                    return existing["molecule_id"]
                raise
        return -1

    def insert_prediction(self, molecule_id: int, property_name: str, predicted_value: float, unit: str, model_version: str = "v1.0-oracle") -> int:
        """
        Inserts a property prediction record linked to a molecule_id via foreign key.
        """
        query = """
        INSERT INTO PropertyPredictions (molecule_id, property_name, predicted_value, unit, model_version)
        VALUES (?, ?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (molecule_id, property_name, predicted_value, unit, model_version))
            conn.commit()
            return cursor.lastrowid

    def log_validation(self, smiles_input: str, is_valid: bool, error_stage: Optional[str] = None, error_message: Optional[str] = None):
        """
        Logs a validation result or chemical exception.
        """
        query = """
        INSERT INTO ValidationLogs (smiles_input, is_valid, error_stage, error_message)
        VALUES (?, ?, ?, ?);
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (smiles_input, is_valid, error_stage, error_message))
            conn.commit()

    def fetch_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetches historical molecules alongside their predicted properties for UI display.
        """
        query = """
        SELECT 
            m.molecule_id,
            m.canonical_smiles,
            m.sa_score,
            m.created_at,
            GROUP_CONCAT(p.property_name || ': ' || p.predicted_value || ' ' || p.unit, ' | ') as predictions
        FROM Molecules m
        LEFT JOIN PropertyPredictions p ON m.molecule_id = p.molecule_id
        GROUP BY m.molecule_id
        ORDER BY m.created_at DESC
        LIMIT ?;
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
