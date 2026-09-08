"""
Comprehensive Test Suite for Chemical Validation, QSPR Prediction,
Inverse Batch Generation, and Exporter Modules.
"""

import os
import sys
import tempfile
import pytest

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.backend.sa_score import calculate_sa_score
from src.backend.validator import validate_and_process_smiles
from src.backend.predictor import PropertyPredictor
from src.backend.generator import PolymerGenerator
from src.backend.exporter import export_to_csv, export_to_sdf


def test_sa_score_calculation():
    # Simple ethanol / acrylate should have low SA score (easy)
    sa_ethanol = calculate_sa_score("CCO")
    assert 1.0 <= sa_ethanol <= 3.0

    # Complex fused/macrocyclic molecule should have higher SA score
    sa_complex = calculate_sa_score("C1CC2CC3CC(C1)C(C2)C3")
    assert sa_complex > sa_ethanol


def test_validation_pipeline_valid_smiles():
    smiles = "CC(=C)C(=O)OCC1CCCCC1"  # Cyclohexyl methacrylate
    result = validate_and_process_smiles(smiles, is_dark_mode=True)
    assert result["is_valid"] is True
    assert result["canonical_smiles"] != ""
    assert result["molecular_weight"] > 0
    assert result["sa_score"] >= 1.0


def test_validation_pipeline_invalid_smiles():
    # Chemically invalid SMILES string
    invalid_smiles = "C1CC(C)CC(="
    result = validate_and_process_smiles(invalid_smiles)
    assert result["is_valid"] is False
    assert "error_stage" in result
    assert result["error_message"] != ""


def test_property_predictor():
    smiles = "CC(=C)C(=O)Oc1ccccc1"  # Phenyl methacrylate
    preds = PropertyPredictor.predict_properties(smiles, target_constraints={"tg": 120.0, "tensile": 50.0})
    
    assert "tg" in preds
    assert "density" in preds
    assert "tensile_strength" in preds
    assert "elasticity" in preds
    assert len(preds["predictions"]) == 4

    # Check error margin dict
    assert "tg" in preds["error_margins"]
    assert "percent_error" in preds["error_margins"]["tg"]


def test_polymer_generator_batch():
    target = {"tg": 180.0, "tensile": 65.0, "elasticity": 2.5}
    candidates = PolymerGenerator.generate_batch(target_properties=target, batch_size=5, max_sa_score=4.5)
    
    assert len(candidates) > 0
    for cand in candidates:
        assert cand["is_valid"] is True
        assert cand["sa_score"] <= 4.5
        assert cand["tg"] is not None
        assert cand["canonical_smiles"] is not None


def test_csv_and_sdf_exporters():
    test_records = [
        {
            "molecule_id": 1,
            "canonical_smiles": "CC(=C)C(=O)OC",
            "sa_score": 1.5,
            "predictions": "Tg: 105 °C | Density: 1.18 g/cm³",
            "created_at": "2026-09-08 12:00:00"
        },
        {
            "molecule_id": 2,
            "canonical_smiles": "C=Cc1ccccc1",
            "sa_score": 1.8,
            "predictions": "Tg: 100 °C | Density: 1.05 g/cm³",
            "created_at": "2026-09-08 12:05:00"
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test_export.csv")
        sdf_path = os.path.join(tmpdir, "test_export.sdf")

        # Test CSV export
        assert export_to_csv(test_records, csv_path) is True
        assert os.path.exists(csv_path)
        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "canonical_smiles" in content
            assert "CC(=C)C(=O)OC" in content

        # Test SDF export
        assert export_to_sdf(test_records, sdf_path) is True
        assert os.path.exists(sdf_path)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
