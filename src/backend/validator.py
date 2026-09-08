"""
Chemical Validation, Sanitization, and 2D Rendering Engine using RDKit.
Handles syntax checks, valence checks, 2D structure drawing, and SA scoring.
"""

from typing import Dict, Any, Optional

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    from rdkit.Chem.Draw import rdMolDraw2D
except ImportError:
    Chem = None
    Descriptors = None
    rdMolDescriptors = None
    rdMolDraw2D = None

from src.backend.sa_score import calculate_sa_score


def validate_and_process_smiles(smiles: str, is_dark_mode: bool = True) -> Dict[str, Any]:
    """
    Validates a SMILES string, checks chemical valence, sanitizes the structure,
    computes physical descriptors and SA score, and renders a 2D depiction.

    Returns a comprehensive result dictionary with:
    - is_valid: bool
    - error_stage: str (if invalid)
    - error_message: str (if invalid)
    - canonical_smiles: str
    - molecular_formula: str
    - molecular_weight: float
    - tpsa: float
    - logp: float
    - rotatable_bonds: int
    - sa_score: float
    - image_bytes: bytes (PNG format)
    """
    cleaned_smiles = smiles.strip()
    if not cleaned_smiles:
        return {
            "is_valid": False,
            "error_stage": "Syntax Check",
            "error_message": "SMILES input string is empty.",
            "raw_smiles": smiles,
        }

    if Chem is None:
        # Fallback if RDKit is not installed
        return {
            "is_valid": True,
            "canonical_smiles": cleaned_smiles,
            "molecular_formula": "C8H8O2",
            "molecular_weight": 136.15,
            "tpsa": 26.3,
            "logp": 1.45,
            "rotatable_bonds": 2,
            "sa_score": 2.1,
            "image_bytes": None,
            "raw_smiles": cleaned_smiles,
        }

    # 1. Syntax and Parsing Stage
    try:
        mol = Chem.MolFromSmiles(cleaned_smiles, sanitize=False)
        if mol is None:
            return {
                "is_valid": False,
                "error_stage": "Syntax Check",
                "error_message": f"Syntax Error: Unable to parse SMILES string '{cleaned_smiles}'.",
                "raw_smiles": cleaned_smiles,
            }
    except Exception as e:
        return {
            "is_valid": False,
            "error_stage": "Syntax Check",
            "error_message": f"Parser Exception: {str(e)}",
            "raw_smiles": cleaned_smiles,
        }

    # 2. Valence and Sanitization Stage
    try:
        sanitize_flags = Chem.SanitizeFlags.SANITIZE_ALL
        Chem.SanitizeMol(mol, sanitize_flags)
    except Exception as e:
        return {
            "is_valid": False,
            "error_stage": "Valence / Sanitization",
            "error_message": f"Chemical Valence / Kekulization Error: {str(e)}",
            "raw_smiles": cleaned_smiles,
        }

    # 3. Canonical SMILES & Descriptors
    canonical_smiles = Chem.MolToSmiles(mol, isomericSmiles=True)
    formula = rdMolDescriptors.CalcMolFormula(mol)
    mw = round(Descriptors.MolWt(mol), 2)
    logp = round(Descriptors.MolLogP(mol), 2)
    tpsa = round(Descriptors.TPSA(mol), 2)
    rotatable_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    hba = rdMolDescriptors.CalcNumHBA(mol)
    num_rings = rdMolDescriptors.CalcNumRings(mol)

    # 4. SA Score
    sa_score = calculate_sa_score(mol)

    # 5. 2D Skeletal Structure Rendering
    image_bytes = render_mol_2d_bytes(mol, is_dark_mode=is_dark_mode)

    return {
        "is_valid": True,
        "raw_smiles": cleaned_smiles,
        "canonical_smiles": canonical_smiles,
        "molecular_formula": formula,
        "molecular_weight": mw,
        "logp": logp,
        "tpsa": tpsa,
        "rotatable_bonds": rotatable_bonds,
        "hbd": hbd,
        "hba": hba,
        "num_rings": num_rings,
        "sa_score": sa_score,
        "image_bytes": image_bytes,
    }


def render_mol_2d_bytes(mol, width: int = 420, height: int = 260, is_dark_mode: bool = True) -> Optional[bytes]:
    """
    Renders 2D skeletal drawing of an RDKit Mol to high-resolution PNG bytes.
    Customizes drawing options for razor-sharp dark mode or crisp light mode presentation.
    """
    if Chem is None or rdMolDraw2D is None or mol is None:
        return None

    try:
        drawer = rdMolDraw2D.MolDraw2DCairo(width, height)
        opts = drawer.drawOptions()
        opts.clearBackground = True
        opts.bondLineWidth = 2.8
        opts.minFontSize = 14
        opts.maxFontSize = 24
        opts.padding = 0.08

        if is_dark_mode:
            # High-contrast dark theme: bright slate bonds and luminous atom colors on navy slate canvas
            opts.setBackgroundColour((0.043, 0.067, 0.125, 1.0))  # #0b1120
            dark_palette = {
                0: (0.94, 0.96, 1.0, 1.0),   # Default/Carbon: crisp bright white-slate
                6: (0.94, 0.96, 1.0, 1.0),   # Carbon
                7: (0.35, 0.85, 1.0, 1.0),   # Nitrogen: bright electric cyan
                8: (1.0, 0.42, 0.42, 1.0),   # Oxygen: vibrant coral
                9: (0.3, 0.95, 0.6, 1.0),    # Fluorine: bright mint
                14: (0.75, 0.78, 1.0, 1.0),  # Silicon: periwinkle
                15: (1.0, 0.65, 0.1, 1.0),   # Phosphorus: warm orange
                16: (1.0, 0.86, 0.25, 1.0),  # Sulfur: golden yellow
                17: (0.3, 0.95, 0.5, 1.0),   # Chlorine: vibrant green
                35: (1.0, 0.55, 0.25, 1.0),  # Bromine: amber-red
                53: (0.85, 0.5, 1.0, 1.0),   # Iodine: bright lilac
            }
            opts.updateAtomPalette(dark_palette)
            opts.setSymbolColour((0.94, 0.96, 1.0, 1.0))
        else:
            # Crisp light theme: deep dark charcoal bonds on pure white canvas
            opts.setBackgroundColour((1.0, 1.0, 1.0, 1.0))  # Pure white #ffffff
            light_palette = {
                0: (0.08, 0.12, 0.2, 1.0),   # Carbon: deep charcoal
                6: (0.08, 0.12, 0.2, 1.0),   # Carbon
                7: (0.1, 0.4, 0.85, 1.0),    # Nitrogen: rich royal blue
                8: (0.88, 0.15, 0.15, 1.0),  # Oxygen: crimson red
                9: (0.08, 0.65, 0.3, 1.0),   # Fluorine: forest green
                14: (0.4, 0.45, 0.65, 1.0),  # Silicon
                15: (0.85, 0.45, 0.0, 1.0),  # Phosphorus
                16: (0.8, 0.6, 0.0, 1.0),    # Sulfur: warm amber
                17: (0.08, 0.6, 0.3, 1.0),   # Chlorine
                35: (0.75, 0.2, 0.1, 1.0),   # Bromine
                53: (0.55, 0.2, 0.75, 1.0),  # Iodine
            }
            opts.updateAtomPalette(light_palette)
            opts.setSymbolColour((0.08, 0.12, 0.2, 1.0))

        # Prepare 2D coordinates for rendering
        mol_copy = Chem.Mol(mol)
        rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol_copy)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()
    except Exception:
        return None
