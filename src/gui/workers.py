import time
from PyQt6.QtCore import QThread, pyqtSignal

class MockValidationWorker(QThread):
    """
    Asynchronous QThread worker for executing RDKit chemical validation 
    and AI prediction workloads without locking the desktop main GUI thread.
    """
    # Signals emitted to update GUI components
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error_raised = pyqtSignal(str)

    def __init__(self, mode: str, payload: dict):
        super().__init__()
        self.mode = mode  # 'forward' or 'inverse'
        self.payload = payload

    def run(self):
        try:
            self.progress_updated.emit(20, "Initiating Pipe-and-Filter processing...")
            time.sleep(0.4)

            if self.mode == "forward":
                smiles = self.payload.get("smiles", "").strip()
                if not smiles:
                    self.error_raised.emit("Error: Input SMILES string is empty.")
                    return

                self.progress_updated.emit(50, "Executing RDKit syntax & valence sanitization...")
                time.sleep(0.5)

                # Mock validation output (Will be replaced by Backend team's RDKit function)
                if "CCCC" in smiles or "C" in smiles:
                    canonical = smiles.upper()
                    sa_score = 2.45
                    tg_val = 165.8
                    density_val = 1.18

                    self.progress_updated.emit(80, "Forward Oracle predicting Tg & density...")
                    time.sleep(0.4)

                    result = {
                        "is_valid": True,
                        "raw_smiles": smiles,
                        "canonical_smiles": canonical,
                        "sa_score": sa_score,
                        "predictions": [
                            {"name": "Glass Transition Temp (Tg)", "value": tg_val, "unit": "°C"},
                            {"name": "Density", "value": density_val, "unit": "g/cm³"}
                        ],
                        "message": "Valid monomer structure processed successfully."
                    }
                    self.progress_updated.emit(100, "Processing complete.")
                    self.finished.emit(result)
                else:
                    self.error_raised.emit(f"Chemical Validation Error: Invalid SMILES syntax '{smiles}'")

            elif self.mode == "inverse":
                self.progress_updated.emit(50, "Running Generative AI inverse design model...")
                time.sleep(0.6)

                target_tg = self.payload.get("target_tg", 150.0)
                generated_smiles = f"CC(C)C(=O)O_{int(target_tg)}"

                result = {
                    "is_valid": True,
                    "canonical_smiles": generated_smiles,
                    "sa_score": 1.95,
                    "predictions": [
                        {"name": "Glass Transition Temp (Tg)", "value": target_tg, "unit": "°C"},
                        {"name": "Density", "value": 1.22, "unit": "g/cm³"}
                    ],
                    "message": "Candidate monomer generated for target parameters."
                }
                self.progress_updated.emit(100, "Generation complete.")
                self.finished.emit(result)

        except Exception as e:
            self.error_raised.emit(f"System Exception: {str(e)}")
