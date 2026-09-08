"""
Asynchronous QThread Workers for AI Polymer Generation and Validation Pipeline.
Runs computationally intensive chemical validation, RDKit rendering, and generative AI
in background threads to prevent UI locking.
"""

import time
from typing import Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal

from src.backend.validator import validate_and_process_smiles
from src.backend.predictor import PropertyPredictor
from src.backend.generator import PolymerGenerator


class PipelineWorker(QThread):
    """
    Background worker thread executing forward chemical validation, QSPR predictions,
    and inverse batch monomer generation.
    """
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    batch_finished = pyqtSignal(list)
    error_raised = pyqtSignal(str)

    def __init__(self, mode: str, payload: dict, is_dark_mode: bool = True):
        super().__init__()
        self.mode = mode  # 'forward' or 'inverse'
        self.payload = payload
        self.is_dark_mode = is_dark_mode

    def run(self):
        try:
            self.progress_updated.emit(15, "Initiating chemical informatics pipeline...")

            if self.mode == "forward":
                smiles = self.payload.get("smiles", "").strip()
                if not smiles:
                    self.error_raised.emit("Error: Input SMILES string is empty.")
                    return

                self.progress_updated.emit(40, "Executing RDKit syntax, valence, and sanitization checks...")
                processed = validate_and_process_smiles(smiles, is_dark_mode=self.is_dark_mode)

                if not processed["is_valid"]:
                    err_msg = f"{processed.get('error_stage', 'Validation')}: {processed.get('error_message', 'Invalid chemical structure.')}"
                    self.error_raised.emit(err_msg)
                    return

                self.progress_updated.emit(75, "Running Forward QSPR models (Tg, Density, Tensile, Modulus)...")
                preds = PropertyPredictor.predict_properties(processed["canonical_smiles"])

                result = {
                    **processed,
                    "predictions": preds["predictions"],
                    "error_margins": preds["error_margins"],
                    "tg": preds["tg"],
                    "density": preds["density"],
                    "tensile_strength": preds["tensile_strength"],
                    "elasticity": preds["elasticity"],
                    "message": "Valid monomer structure processed and rendered successfully."
                }

                self.progress_updated.emit(100, "Pipeline completed successfully.")
                self.finished.emit(result)

            elif self.mode == "inverse":
                self.progress_updated.emit(35, "Searching chemical polymer design space...")
                target_tg = float(self.payload.get("target_tg", 160.0))
                target_tensile = float(self.payload.get("target_tensile", 70.0))
                target_elasticity = float(self.payload.get("target_elasticity", 2.5))
                max_sa = float(self.payload.get("max_sa", 4.5))
                batch_size = int(self.payload.get("batch_size", 10))

                target_dict = {
                    "tg": target_tg,
                    "tensile": target_tensile,
                    "elasticity": target_elasticity
                }

                self.progress_updated.emit(65, "Filtering candidates via RDKit valence & SA score threshold...")
                candidates = PolymerGenerator.generate_batch(
                    target_properties=target_dict,
                    batch_size=batch_size,
                    max_sa_score=max_sa,
                    is_dark_mode=self.is_dark_mode
                )

                if not candidates:
                    self.error_raised.emit("No candidate polymers met the target constraints. Try relaxing the SA score threshold.")
                    return

                self.progress_updated.emit(100, f"Generated {len(candidates)} viable polymer candidate(s).")
                # Emit best candidate for immediate view and full batch
                self.finished.emit(candidates[0])
                self.batch_finished.emit(candidates)

        except Exception as e:
            self.error_raised.emit(f"Pipeline Execution Error: {str(e)}")


# Maintain backward compatibility alias
MockValidationWorker = PipelineWorker
