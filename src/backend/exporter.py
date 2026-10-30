"""
Dataset and Molecular Exporter for Polymer Informatics.
Exports records to CSV and SDF (Structure-Data File) formats for downstream lab modeling.
"""

import csv
from typing import List, Dict, Any

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
except ImportError:
    Chem = None
    AllChem = None
    Descriptors = None
    rdMolDescriptors = None


def export_to_csv(records: List[Dict[str, Any]], filepath: str) -> bool:
    """
    Exports a list of polymer molecular records to a CSV file.
    If molecular descriptors (formula, MW, TPSA, LogP) are missing from database records,
    they are automatically computed from the canonical SMILES using RDKit.
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

    # Ensure all fieldnames exist in dicts; derive descriptors if absent
    clean_rows = []
    for r in records:
        row = {}
        for f in fieldnames:
            row[f] = r.get(f, "")

        # Auto-compute molecular descriptors if not already present
        if Chem is not None and Descriptors is not None and rdMolDescriptors is not None:
            if not row["molecular_formula"] or not row["molecular_weight"]:
                smiles = row["canonical_smiles"] or r.get("smiles_string")
                if smiles:
                    try:
                        mol = Chem.MolFromSmiles(str(smiles))
                        if mol:
                            if not row["molecular_formula"]:
                                row["molecular_formula"] = rdMolDescriptors.CalcMolFormula(mol)
                            if not row["molecular_weight"]:
                                row["molecular_weight"] = round(Descriptors.MolWt(mol), 2)
                            if not row["tpsa"]:
                                row["tpsa"] = round(Descriptors.TPSA(mol), 2)
                            if not row["logp"]:
                                row["logp"] = round(Descriptors.MolLogP(mol), 2)
                    except Exception:
                        pass

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

            # Auto-compute & include descriptors if missing
            formula = r.get("molecular_formula")
            mw = r.get("molecular_weight")
            tpsa = r.get("tpsa")
            logp = r.get("logp")

            if Descriptors is not None and rdMolDescriptors is not None:
                if not formula:
                    formula = rdMolDescriptors.CalcMolFormula(mol)
                if not mw:
                    mw = round(Descriptors.MolWt(mol), 2)
                if not tpsa:
                    tpsa = round(Descriptors.TPSA(mol), 2)
                if not logp:
                    logp = round(Descriptors.MolLogP(mol), 2)

            if formula:
                mol.SetProp("MOLECULAR_FORMULA", str(formula))
            if mw:
                mol.SetProp("MOLECULAR_WEIGHT", str(mw))
            if tpsa is not None:
                mol.SetProp("TPSA", str(tpsa))
            if logp is not None:
                mol.SetProp("LOGP", str(logp))

            writer.write(mol)
    finally:
        writer.close()

    return True
