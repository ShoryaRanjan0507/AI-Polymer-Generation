import joblib
import numpy as np
from typing import Dict, Any, Optional

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors, rdFingerprintGenerator
except ImportError:
    Chem = None
    Descriptors = None
    rdMolDescriptors = None
    rdFingerprintGenerator = None

# 1. Load all three AI models once
try:
    MODEL_TG = joblib.load("model/tg_predictor_gb.pkl")
    MODEL_TENSILE = joblib.load("model/tensile_predictor_gb.pkl")
    MODEL_MODULUS = joblib.load("model/modulus_predictor_gb.pkl")
    MFP_GEN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    print("Successfully loaded all 3 AI models!")
except Exception as e:
    MODEL_TG = None
    MODEL_TENSILE = None
    MODEL_MODULUS = None
    MFP_GEN = None
    print(f"Failed to load AI models: {e}")

class PropertyPredictor:
    """
    Predicts physical properties using the trained HistGradientBoosting Regressors.
    """

    @staticmethod
    def predict_properties(mol_or_smiles, target_constraints: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        if isinstance(mol_or_smiles, str):
            mol = Chem.MolFromSmiles(mol_or_smiles) if Chem else None
        else:
            mol = mol_or_smiles

        # Fallbacks if RDKit or the models fail
        tg_val = 145.0
        density_val = 1.15
        tensile_val = 65.0
        modulus_val = 2.4

        if mol is not None and MODEL_TG is not None and MFP_GEN is not None:
            # 2. Extract Structural Fingerprint (2048 features)
            fingerprint = list(MFP_GEN.GetFingerprint(mol))
            
            # 3. Calculate the exact 6 Physical Descriptors used in training
            mol_wt = Descriptors.MolWt(mol)
            logp = Descriptors.MolLogP(mol)
            tpsa = Descriptors.TPSA(mol)
            hbd = rdMolDescriptors.CalcNumHBD(mol)
            hba = rdMolDescriptors.CalcNumHBA(mol)
            rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
            
            physical_traits = [mol_wt, logp, tpsa, hbd, hba, rotatable]
            
            # 4. Fuse into 2054 features and format for scikit-learn
            combined_features = fingerprint + physical_traits
            features_2d = [combined_features]
            
            # 5. Predict all properties with the AI
            tg_val = round(float(MODEL_TG.predict(features_2d)[0]), 1)
            tensile_val = round(float(MODEL_TENSILE.predict(features_2d)[0]), 1)
            modulus_val = round(float(MODEL_MODULUS.predict(features_2d)[0]), 2)

            # Keep a simple heuristic formula for density since we didn't train an AI for it
            density_val = round(1.05 + (rdMolDescriptors.CalcNumAromaticRings(mol) * 0.08), 2)

        # 6. Format results exactly as your GUI expects
        predictions_list = [
            {"name": "Glass Transition Temp (Tg)", "key": "tg", "value": tg_val, "unit": "°C"},
            {"name": "Polymer Density", "key": "density", "value": density_val, "unit": "g/cm³"},
            {"name": "Tensile Strength", "key": "tensile_strength", "value": tensile_val, "unit": "MPa"},
            {"name": "Elastic Modulus", "key": "elasticity", "value": modulus_val, "unit": "GPa"}
        ]

        # 7. Calculate error margins across all AI predictions
        error_margins = {}
        if target_constraints:
            for key, target_val in target_constraints.items():
                if target_val is not None and target_val != 0:
                    
                    # Match the UI slider key to the correct AI prediction
                    actual_val = tg_val
                    if key in ("tensile", "tensile_strength", "target_tensile_strength"):
                        actual_val = tensile_val
                    elif key in ("modulus", "elasticity", "target_elastic_modulus"):
                        actual_val = modulus_val
                    elif key in ("tg", "target_tg", "target_glass_transition_temp"):
                        actual_val = tg_val

                    abs_error = abs(actual_val - target_val)
                    percent_error = round((abs_error / abs(target_val)) * 100.0, 2)
                    
                    error_margins[key] = {
                        "target": target_val, 
                        "actual": actual_val, 
                        "abs_error": round(abs_error, 2), 
                        "percent_error": percent_error, 
                        "is_hit": percent_error <= 5.0
                    }

        return {
            "predictions": predictions_list,
            "error_margins": error_margins,
            "tg": tg_val,
            "density": density_val,
            "tensile_strength": tensile_val,
            "elasticity": modulus_val
        }