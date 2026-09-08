"""
Generative AI & Inverse Polymer Design Engine.
Generates candidate monomer blueprints tailored to target physical constraints
(Glass Transition Temp Tg, Tensile Strength, Elastic Modulus, SA Score threshold).
Filters unmanufacturable designs, ranks by error margin, and returns rich validated batches.
"""

import random
from typing import List, Dict, Any

try:
    from rdkit import Chem
except ImportError:
    Chem = None

from src.backend.validator import validate_and_process_smiles
from src.backend.predictor import PropertyPredictor


# Curated polymer building blocks & functional motifs across major polymer classes:
# Acrylates, Methacrylates, Polyimides, Polyamides, Polyesters, Polycarbonates, Polyurethanes, Fluoropolymers, Polystyrenics
POLYMER_MOTIF_TEMPLATES = [
    # 1. High-Tg & Rigid Aromatic / Imide Motifs (Tg > 200°C)
    "O=C1NC(=O)c2ccc(Oc3ccc4c(c3)C(=O)NC4=O)cc21",                     # Polyimide core
    "CC(C)(c1ccc(Oc2ccc(C(=O)O)cc2)cc1)c3ccc(Oc4ccc(C(=O)O)cc4)cc3",   # Bisphenol-A ether acid
    "O=C(Cl)c1ccc(C(=O)Cl)cc1",                                         # Terephthaloyl chloride
    "Nc1ccc(Oc2ccc(N)cc2)cc1",                                          # 4,4'-Oxydianiline (Kapton precursor)
    "O=C1OC(=O)c2cc3c(=O)oc(=O)c3cc21",                                 # Pyromellitic dianhydride
    "c1cc(ccc1C(=O)O)c2ccc(cc2)C(=O)O",                                 # Biphenyl dicarboxylic acid
    "O=C(Cl)c1cccc(C(=O)Cl)c1",                                         # Isophthaloyl chloride
    "Nc1ccc(Cc2ccc(N)cc2)cc1",                                          # 4,4'-Methylenedianiline
    "CC1(C)c2cc(C(=O)O)ccc2-c3ccc(C(=O)O)cc31",                        # Fluorene dicarboxylate derivative

    # 2. Moderate-to-High Tg Engineering Thermoplastics (120°C - 200°C)
    "CC(C)(c1ccc(O)cc1)c2ccc(O)cc2",                                    # Bisphenol A
    "C=CC(=O)Oc1ccccc1",                                                # Phenyl acrylate
    "CC(=C)C(=O)Oc1ccccc1",                                             # Phenyl methacrylate
    "C=CC(=O)OCC1CCCCC1",                                               # Cyclohexyl acrylate
    "CC(=C)C(=O)OCC1CCCCC1",                                            # Cyclohexyl methacrylate
    "C=CC(=O)OC12CC3CC(CC(C3)C1)C2",                                    # Adamantyl acrylate
    "CC(=C)C(=O)OC12CC3CC(CC(C3)C1)C2",                                 # Adamantyl methacrylate
    "C=Cc1ccc(C(C)(C)C)cc1",                                            # 4-tert-butylstyrene
    "C=Cc1ccc(OC(=O)C)cc1",                                             # 4-acetoxystyrene
    "C=Cc1ccc(Cl)cc1",                                                  # 4-chlorostyrene
    "O=C(OCC1CO1)c2ccccc2",                                             # Glycidyl benzoate
    "O=C(Cl)CCCCCCCCC(=O)Cl",                                           # Sebacoyl chloride

    # 3. Flexible / Elastomeric Motifs (Tg < 100°C)
    "C=CC(=O)OCCCC",                                                    # n-Butyl acrylate (low Tg ~ -54°C)
    "CC(=C)C(=O)OCCCC",                                                 # n-Butyl methacrylate (Tg ~ 20°C)
    "C=CC(=O)OCCCCCC",                                                  # Hexyl acrylate
    "C=CC(=O)OCCCCCCCC",                                                # Octyl acrylate
    "C=CC(=O)OCCOCCOCCOC",                                              # Triethylene glycol monoether acrylate
    "C=CC(=O)OCC(CC)CCCC",                                              # 2-Ethylhexyl acrylate (Tg ~ -50°C)
    "C=CC(=O)OCCO",                                                     # 2-Hydroxyethyl acrylate
    "CC(=C)C(=O)OCCO",                                                  # 2-Hydroxyethyl methacrylate (HEMA)
    "C=CC(=O)OCCN(C)C",                                                 # DMAEMA analog
    "C=CC(=O)N(C)C",                                                    # N,N-Dimethylacrylamide
    "C=CC(=O)NCC(C)C",                                                  # N-isobutylacrylamide
    "O=C(O)CCCC(=O)O",                                                  # Adipic acid

    # 4. High-Performance Fluorinated / Specialty Motifs
    "C=CC(=O)OCC(F)(F)C(F)(F)F",                                        # 2,2,3,3,3-Pentafluoropropyl acrylate
    "CC(=C)C(=O)OCC(F)(F)C(F)(F)F",                                     # Fluorinated methacrylate
    "C=CC(=O)OCC(F)(F)C(F)(F)C(F)(F)C(F)(F)F",                          # Heptafluorobutyl acrylate
    "C=CC(=O)O[Si](C)(C)O[Si](C)(C)C",                                  # Siloxane acrylate
]


class PolymerGenerator:
    """
    Inverse design generator that searches the chemical polymer space
    to identify candidate molecules matching specified physical properties.
    """

    @classmethod
    def generate_batch(
        cls,
        target_properties: Dict[str, float],
        batch_size: int = 15,
        max_sa_score: float = 4.5,
        is_dark_mode: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generates and validates a batch of polymer candidate monomers.
        Filters out invalid structures and those exceeding max SA score.
        Sorts candidates by aggregate property closeness (hit quality).
        """
        target_tg = target_properties.get("tg", target_properties.get("target_tg", 160.0))
        target_tensile = target_properties.get("tensile", target_properties.get("target_tensile", 70.0))
        target_elasticity = target_properties.get("elasticity", target_properties.get("target_elasticity", 2.5))

        target_dict = {
            "tg": target_tg,
            "tensile": target_tensile,
            "elasticity": target_elasticity
        }

        candidates = []
        sampled_smiles_set = set()

        # Generate candidate pool
        pool = list(POLYMER_MOTIF_TEMPLATES)
        random.shuffle(pool)

        # Build candidate variants
        for base_smiles in pool:
            variants = cls._create_variations(base_smiles, target_tg)
            for s in variants:
                if s not in sampled_smiles_set:
                    sampled_smiles_set.add(s)

        # Process and validate candidates
        valid_candidates = []
        for s in sampled_smiles_set:
            processed = validate_and_process_smiles(s, is_dark_mode=is_dark_mode)
            if not processed["is_valid"]:
                continue

            sa = processed.get("sa_score", 10.0)
            if sa > max_sa_score:
                continue

            # Forward predict properties
            pred_results = PropertyPredictor.predict_properties(s, target_constraints=target_dict)
            
            # Compute total distance / error score
            tg_err = abs(pred_results["tg"] - target_tg) / max(abs(target_tg), 1.0)
            tensile_err = abs(pred_results["tensile_strength"] - target_tensile) / max(abs(target_tensile), 1.0)
            modulus_err = abs(pred_results["elasticity"] - target_elasticity) / max(abs(target_elasticity), 1.0)

            # Weight property closeness (Tg 50%, Tensile 30%, Modulus 20%)
            total_weighted_error = (0.5 * tg_err) + (0.3 * tensile_err) + (0.2 * modulus_err)

            candidate_data = {
                **processed,
                "predictions": pred_results["predictions"],
                "error_margins": pred_results["error_margins"],
                "tg": pred_results["tg"],
                "density": pred_results["density"],
                "tensile_strength": pred_results["tensile_strength"],
                "elasticity": pred_results["elasticity"],
                "total_error": total_weighted_error,
                "is_hit": any(v.get("is_hit", False) for v in pred_results["error_margins"].values()),
                "message": f"Generated candidate monomer matching target Tg ({target_tg}°C) with SA score {sa}."
            }
            valid_candidates.append(candidate_data)

        # Sort by total error (lowest error first)
        valid_candidates.sort(key=lambda x: x["total_error"])

        return valid_candidates[:batch_size]

    @classmethod
    def _create_variations(cls, base_smiles: str, target_tg: float) -> List[str]:
        """
        Creates structurally valid monomer variations tuned towards target thermal profile.
        """
        variations = [base_smiles]

        # Alkyl chain tuning: long chains decrease Tg, methyl/aromatic increase Tg
        if target_tg > 180.0:
            # Shift towards aromatic/rigid variants
            variations.append(base_smiles.replace("C=CC(=O)O", "CC(=C)C(=O)O"))
            if "OCCCC" in base_smiles:
                variations.append(base_smiles.replace("OCCCC", "Oc1ccccc1"))
        elif target_tg < 80.0:
            # Shift towards flexible chains
            if "C(=O)O" in base_smiles:
                variations.append(base_smiles.replace("C(=O)O", "C(=O)OCCCCCC"))

        return variations
