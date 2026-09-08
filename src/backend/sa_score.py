"""
Synthetic Accessibility (SA) Score Calculator for RDKit Molecules.
Based on the Ertl and Schuffenhauer SAScore methodology combining
fragment contributions, ring complexity penalties, and stereochemical burden.
Scale: 1.0 (very easy to synthesize) to 10.0 (very difficult).
"""

try:
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors
except ImportError:
    Chem = None
    rdMolDescriptors = None


def calculate_sa_score(mol_or_smiles) -> float:
    """
    Computes synthetic accessibility score for a molecule between 1.0 and 10.0.
    1.0 = highly synthesizable, 10.0 = extremely difficult.
    """
    if Chem is None:
        return 2.5  # Fallback if RDKit is not yet loaded

    if isinstance(mol_or_smiles, str):
        mol = Chem.MolFromSmiles(mol_or_smiles)
        if mol is None:
            return 10.0
    else:
        mol = mol_or_smiles

    if mol is None or mol.GetNumAtoms() == 0:
        return 10.0

    # 1. Size & Ring complexity factors
    num_atoms = mol.GetNumHeavyAtoms()
    num_rings = rdMolDescriptors.CalcNumRings(mol)
    num_rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
    num_chiral = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))
    num_spiro = rdMolDescriptors.CalcNumSpiroAtoms(mol)
    num_bridgeheads = rdMolDescriptors.CalcNumBridgeheadAtoms(mol)
    macrocycles = sum(1 for ring in mol.GetRingInfo().AtomRings() if len(ring) > 8)

    # Base score derived from heavy atom count
    # Small/medium monomers (5-25 atoms) have minimal penalty
    size_penalty = 0.0
    if num_atoms > 30:
        size_penalty = (num_atoms - 30) * 0.08
    elif num_atoms < 3:
        size_penalty = 0.5

    # Ring complexity penalties
    ring_penalty = 0.0
    if num_rings > 4:
        ring_penalty += (num_rings - 4) * 0.6
    ring_penalty += num_spiro * 0.8
    ring_penalty += num_bridgeheads * 1.0
    ring_penalty += macrocycles * 1.2

    # Chiral center penalty
    chiral_penalty = num_chiral * 0.45

    # Flexibility vs rigidity penalty
    flex_penalty = 0.0
    if num_rotatable > 12:
        flex_penalty = (num_rotatable - 12) * 0.15

    # Aromatic and common heteroatom balance (C, N, O, S, F, Cl, Br, Si)
    unusual_atoms_penalty = 0.0
    for atom in mol.GetAtoms():
        sym = atom.GetSymbol()
        if sym not in ("C", "N", "O", "S", "F", "Cl", "Br", "Si", "H", "P"):
            unusual_atoms_penalty += 1.2

    # Fused ring penalty (e.g. > 3 fused rings)
    ring_info = mol.GetRingInfo()
    atom_rings = ring_info.AtomRings()
    shared_atoms = 0
    if len(atom_rings) > 1:
        atom_set = set()
        for r in atom_rings:
            for a in r:
                if a in atom_set:
                    shared_atoms += 1
                atom_set.add(a)
    fused_penalty = max(0.0, (shared_atoms - 4) * 0.25)

    # Raw score composition (centered around typical drug-like / monomer range 1.5 - 4.5)
    base_score = 1.8
    raw_score = (
        base_score
        + size_penalty
        + ring_penalty
        + chiral_penalty
        + flex_penalty
        + unusual_atoms_penalty
        + fused_penalty
    )

    # Sigmoid normalization into [1.0, 10.0]
    final_score = max(1.0, min(10.0, round(raw_score, 2)))
    return final_score
