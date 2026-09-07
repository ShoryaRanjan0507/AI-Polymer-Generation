import os
import sys

# Ensure src is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.database_manager import DatabaseManager

def test_database_initialization_and_crud():
    db = DatabaseManager(":memory:")
    mol_id = db.insert_molecule(smiles_string="cco", canonical_smiles="CCO", sa_score=2.1)
    assert mol_id > 0
    dup_id = db.insert_molecule(smiles_string="occ", canonical_smiles="CCO", sa_score=2.1)
    assert dup_id == mol_id
    pred_id = db.insert_prediction(molecule_id=mol_id, property_name="Glass Transition Temp (Tg)", predicted_value=165.5, unit="°C")
    assert pred_id > 0
    history = db.fetch_history(limit=10)
    assert len(history) == 1
    assert history[0]["canonical_smiles"] == "CCO"
    assert "Glass Transition Temp" in history[0]["predictions"]

def run_tests():
    print("Executing SQLite In-Memory Database Tests...")
    test_database_initialization_and_crud()
    print("  [PASSED] All database CRUD and constraint assertions passed!")
    print("\nAll Database In-Memory Tests Passed Successfully!")

if __name__ == "__main__":
    run_tests()


