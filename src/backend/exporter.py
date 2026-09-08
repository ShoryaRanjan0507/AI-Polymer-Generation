"""
Dataset and Molecular Exporter for Polymer Informatics.
Exports records to CSV and SDF (Structure-Data File) formats for downstream lab modeling.
"""

import csv
from typing import List, Dict, Any

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except ImportError:
    Chem = None
    AllChem = None


def export_to_csv(records: List[Dict[str, Any]], filepath: str) -> bool:
    """
    Exports a list of polymer molecular records to a CSV file.
    """
    if not records:
        return False

    fieldnames = [
        "molecule_id",
        "canonical_smiles",
        "sa_score",
        "created_at",
        "predictions",
        "molecular_formula",
        "molecular_weight",
        "tpsa",
        "logp"
    ]

    # Ensure all fieldnames exist in dicts
    clean_rows = []
    for r in records:
        row = {}
        for f in fieldnames:
            row[f] = r.get(f, "")
        clean_rows.append(row)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_rows)

    return True


def export_to_sdf(records: List[Dict[str, Any]], filepath: str) -> bool:
    """
    Exports molecular records to an SDF file with 2D computed coordinates and property tags.
    """
    if Chem is None or not records:
        return False

    writer = Chem.SDWriter(filepath)
    try:
        for r in records:
            smiles = r.get("canonical_smiles") or r.get("smiles_string")
            if not smiles:
                continue

            mol = Chem.MolFromSmiles(str(smiles))
            if mol is None:
                continue

            # Compute 2D coordinates
            AllChem.Compute2DCoords(mol)

            # Set property metadata tags
            if r.get("molecule_id"):
                mol.SetProp("MOLECULE_ID", str(r.get("molecule_id")))
            if r.get("sa_score") is not None:
                mol.SetProp("SA_SCORE", str(r.get("sa_score")))
            if r.get("predictions"):
                mol.SetProp("PREDICTIONS", str(r.get("predictions")))
            if r.get("created_at"):
                mol.SetProp("CREATED_AT", str(r.get("created_at")))

            writer.write(mol)
    finally:
        writer.close()

    return True
