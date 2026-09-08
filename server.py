"""
Interactive Development Server and REST API for Polymer Property Prediction & Generation.
Supports both REST endpoints and an integrated web GUI for testing the backend pipeline.
"""

import os
import sys
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.database.database_manager import DatabaseManager
from src.backend.validator import validate_and_process_smiles
from src.backend.predictor import PropertyPredictor
from src.backend.generator import PolymerGenerator
from src.backend.exporter import export_to_csv, export_to_sdf

app = FastAPI(
    title="AI Polymer Generation & Prediction Platform",
    description="Backend API and Development Server for Polymer Informatics",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseManager("polymer_data.db")


# Request schemas
class PredictRequest(BaseModel):
    smiles: str
    target_tg: Optional[float] = None
    target_tensile: Optional[float] = None
    target_elasticity: Optional[float] = None
    is_dark_mode: bool = True


class GenerateRequest(BaseModel):
    target_tg: float = 160.0
    target_tensile: float = 70.0
    target_elasticity: float = 2.5
    max_sa_score: float = 4.5
    batch_size: int = 10
    is_dark_mode: bool = True


class SaveRecordRequest(BaseModel):
    smiles_string: str
    canonical_smiles: str
    sa_score: Optional[float] = None
    predictions: List[Dict[str, Any]] = []


@app.post("/api/predict")
def api_predict(req: PredictRequest):
    """
    Validates a SMILES string, calculates SA score, molecular descriptors,
    and forward-predicts thermal & mechanical properties.
    """
    processed = validate_and_process_smiles(req.smiles, is_dark_mode=req.is_dark_mode)
    if not processed["is_valid"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error_stage": processed.get("error_stage", "Validation"),
                "error_message": processed.get("error_message", "Invalid SMILES structure.")
            }
        )

    targets = {}
    if req.target_tg is not None:
        targets["tg"] = req.target_tg
    if req.target_tensile is not None:
        targets["tensile"] = req.target_tensile
    if req.target_elasticity is not None:
        targets["elasticity"] = req.target_elasticity

    preds = PropertyPredictor.predict_properties(processed["canonical_smiles"], target_constraints=targets if targets else None)

    # Convert binary image to base64 if present
    import base64
    img_b64 = None
    if processed.get("image_bytes"):
        img_b64 = base64.b64encode(processed["image_bytes"]).decode("utf-8")

    return {
        "is_valid": True,
        "raw_smiles": processed.get("raw_smiles"),
        "canonical_smiles": processed.get("canonical_smiles"),
        "molecular_formula": processed.get("molecular_formula"),
        "molecular_weight": processed.get("molecular_weight"),
        "logp": processed.get("logp"),
        "tpsa": processed.get("tpsa"),
        "rotatable_bonds": processed.get("rotatable_bonds"),
        "sa_score": processed.get("sa_score"),
        "predictions": preds["predictions"],
        "error_margins": preds["error_margins"],
        "tg": preds["tg"],
        "density": preds["density"],
        "tensile_strength": preds["tensile_strength"],
        "elasticity": preds["elasticity"],
        "image_base64": img_b64
    }


@app.post("/api/generate")
def api_generate(req: GenerateRequest):
    """
    Generates a candidate batch of polymer monomers tailored to target physical constraints.
    """
    target_dict = {
        "tg": req.target_tg,
        "tensile": req.target_tensile,
        "elasticity": req.target_elasticity
    }

    candidates = PolymerGenerator.generate_batch(
        target_properties=target_dict,
        batch_size=req.batch_size,
        max_sa_score=req.max_sa_score,
        is_dark_mode=req.is_dark_mode
    )

    # Encode images to base64
    import base64
    for c in candidates:
        if c.get("image_bytes"):
            c["image_base64"] = base64.b64encode(c["image_bytes"]).decode("utf-8")
            c.pop("image_bytes", None)

    return {
        "count": len(candidates),
        "target": target_dict,
        "max_sa_score": req.max_sa_score,
        "candidates": candidates
    }


@app.get("/api/history")
def api_get_history(limit: int = 100):
    """
    Retrieves catalog of past molecules and predictions from SQLite.
    """
    records = db.fetch_history(limit=limit)
    return {"records": records}


@app.post("/api/history")
def api_save_history(req: SaveRecordRequest):
    """
    Saves a molecule record and associated property predictions to SQLite.
    """
    try:
        mol_id = db.insert_molecule(req.smiles_string, req.canonical_smiles, req.sa_score)
        for p in req.predictions:
            db.insert_prediction(mol_id, p["name"], float(p["value"]), p["unit"])
        return {"status": "success", "molecule_id": mol_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/csv")
def api_export_csv():
    """
    Exports database history as a downloadable CSV file.
    """
    import tempfile
    records = db.fetch_history(limit=500)
    temp_file = os.path.join(tempfile.gettempdir(), "polymer_history.csv")
    export_to_csv(records, temp_file)
    return FileResponse(temp_file, media_type="text/csv", filename="polymer_history.csv")


@app.get("/api/export/sdf")
def api_export_sdf():
    """
    Exports database history as a downloadable SDF file.
    """
    import tempfile
    records = db.fetch_history(limit=500)
    temp_file = os.path.join(tempfile.gettempdir(), "polymer_history.sdf")
    export_to_sdf(records, temp_file)
    return FileResponse(temp_file, media_type="chemical/x-mdl-sdfile", filename="polymer_history.sdf")


@app.get("/", response_class=HTMLResponse)
def index_page():
    """
    Serves modern development laboratory dashboard UI.
    """
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Polymer Generation & Property Prediction</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #090d16;
            --bg-secondary: #0f172a;
            --bg-card: rgba(30, 41, 59, 0.7);
            --border-color: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-cyan: #38bdf8;
            --accent-blue: #0284c7;
            --accent-emerald: #10b981;
            --accent-purple: #8b5cf6;
            --accent-rose: #f43f5e;
            --glass-blur: blur(12px);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Outfit', sans-serif;
            background: radial-gradient(circle at 10% 20%, #0f172a 0%, #090d16 90%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            padding: 16px 32px;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: var(--glass-blur);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .brand-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #0284c7, #8b5cf6);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 18px;
            box-shadow: 0 0 15px rgba(2, 132, 199, 0.4);
        }
        .brand-title {
            font-size: 20px;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(90deg, #f8fafc, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .badge {
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-cyan);
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .main-container {
            flex: 1;
            padding: 24px 32px;
            display: grid;
            grid-template-columns: 1.25fr 0.95fr;
            gap: 24px;
            max-width: 1600px;
            margin: 0 auto;
            width: 100%;
        }

        .panel-left, .panel-right {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .tabs-header {
            display: flex;
            gap: 8px;
            background: rgba(15, 23, 42, 0.6);
            padding: 6px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
        }
        .tab-btn {
            flex: 1;
            padding: 10px 16px;
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 14px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: 'Outfit', sans-serif;
        }
        .tab-btn.active {
            background: var(--accent-blue);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.35);
        }

        .card {
            background: var(--bg-card);
            backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
        }

        .form-group {
            margin-bottom: 16px;
        }
        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 6px;
        }
        .form-group input, .form-group select {
            width: 100%;
            background: #090d16;
            border: 1px solid var(--border-color);
            padding: 10px 14px;
            border-radius: 8px;
            color: var(--text-main);
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            transition: border 0.2s;
        }
        .form-group input:focus, .form-group select:focus {
            outline: none;
            border-color: var(--accent-cyan);
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
        }

        .slider-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
        }
        .slider-val {
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-cyan);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }
        input[type=range] {
            width: 100%;
            height: 6px;
            background: #1e293b;
            border-radius: 3px;
            outline: none;
            -webkit-appearance: none;
        }
        input[type=range]::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: var(--accent-cyan);
            cursor: pointer;
            box-shadow: 0 0 8px rgba(56, 189, 248, 0.8);
        }

        .btn-primary {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #0284c7, #2563eb);
            border: none;
            border-radius: 8px;
            color: #ffffff;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
        }
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(2, 132, 199, 0.5);
        }
        .btn-emerald {
            background: linear-gradient(135deg, #059669, #10b981);
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
        }
        .btn-emerald:hover {
            box-shadow: 0 6px 18px rgba(16, 185, 129, 0.5);
        }

        .viewport-box {
            min-height: 240px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #090d16;
            border: 2px dashed var(--border-color);
            border-radius: 10px;
            padding: 16px;
            text-align: center;
        }
        .viewport-box img {
            max-width: 100%;
            max-height: 220px;
            border-radius: 6px;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }
        .metric-card {
            background: #090d16;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }
        .metric-title {
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }
        .metric-val {
            font-size: 18px;
            font-weight: 800;
            color: var(--accent-cyan);
            font-family: 'JetBrains Mono', monospace;
        }
        .metric-card.wide {
            grid-column: span 2;
        }

        .table-wrap {
            overflow-x: auto;
            max-height: 320px;
            margin-top: 12px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        th {
            background: #0f172a;
            color: var(--accent-cyan);
            text-align: left;
            padding: 10px;
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #1e293b;
            color: var(--text-main);
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
        }
        tr:hover td {
            background: rgba(56, 189, 248, 0.08);
            cursor: pointer;
        }

        .status-footer {
            padding: 12px 32px;
            background: #090d16;
            border-top: 1px solid var(--border-color);
            font-size: 13px;
            color: var(--text-muted);
            display: flex;
            justify-content: space-between;
        }

        .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 12px;
        }
        .btn-secondary {
            flex: 1;
            padding: 10px;
            background: #1e293b;
            border: 1px solid var(--border-color);
            color: var(--text-main);
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
        }
        .btn-secondary:hover { background: #334155; }
    </style>
</head>
<body>

<header>
    <div class="brand">
        <div class="brand-icon">P</div>
        <div class="brand-title">AI Polymer Generation & Property Oracle</div>
        <span class="badge">RDKit & SQLite Backend</span>
    </div>
    <div style="display:flex; gap:10px;">
        <button class="tab-btn" onclick="fetchHistory()" style="background:#1e293b; color:#fff;">Sync SQLite DB</button>
    </div>
</header>

<div class="main-container">
    <!-- Left Panel: Interactive Workflow Tabs -->
    <div class="panel-left">
        <div class="tabs-header">
            <button class="tab-btn active" onclick="switchTab('tab-forward')">Forward Prediction</button>
            <button class="tab-btn" onclick="switchTab('tab-inverse')">Inverse AI Design</button>
            <button class="tab-btn" onclick="switchTab('tab-history')">Database History</button>
        </div>

        <!-- Tab 1: Forward Prediction -->
        <div id="tab-forward" class="card tab-content">
            <h3 style="margin-bottom:8px; font-size:16px;">Forward Chemical Validation & Property Prediction</h3>
            <p style="color:var(--text-muted); font-size:13px; margin-bottom:16px;">
                Enter a monomer or polymer repeat unit SMILES representation to sanitize chemical valence, compute SA score, and predict physical properties.
            </p>

            <div class="form-group">
                <label>Monomer SMILES String:</label>
                <input type="text" id="smiles_input" value="CC(=C)C(=O)Oc1ccccc1" placeholder="e.g. CCO, C=CC(=O)OCCCC">
            </div>

            <div style="display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap;">
                <span style="font-size:12px; color:var(--text-muted); align-self:center;">Examples:</span>
                <button class="btn-secondary" style="flex:none; padding:4px 10px; font-size:12px;" onclick="setSmiles('CC(=C)C(=O)Oc1ccccc1')">Phenyl Methacrylate</button>
                <button class="btn-secondary" style="flex:none; padding:4px 10px; font-size:12px;" onclick="setSmiles('O=C1NC(=O)c2ccc(Oc3ccc4c(c3)C(=O)NC4=O)cc21')">Kapton Core</button>
                <button class="btn-secondary" style="flex:none; padding:4px 10px; font-size:12px;" onclick="setSmiles('C=CC(=O)OCCCC')">Butyl Acrylate</button>
            </div>

            <button class="btn-primary" onclick="runForwardPrediction()">Validate Structure & Predict Properties</button>

            <div id="desc_box" style="margin-top:16px; font-size:13px; color:var(--text-muted); line-height:1.6;"></div>
        </div>

        <!-- Tab 2: Inverse AI Generation -->
        <div id="tab-inverse" class="card tab-content" style="display:none;">
            <h3 style="margin-bottom:8px; font-size:16px;">Conditional Inverse Monomer Generation</h3>
            <p style="color:var(--text-muted); font-size:13px; margin-bottom:16px;">
                Specify target thermomechanical constraints. The generative pipeline searches and filters polymer space, retaining only lab-synthesizable candidates.
            </p>

            <div class="form-group">
                <div class="slider-row">
                    <label>Target Glass Transition Temp (Tg, °C):</label>
                    <span id="lbl_target_tg" class="slider-val">180.0 °C</span>
                </div>
                <input type="range" id="slider_tg" min="-50" max="300" value="180" oninput="document.getElementById('lbl_target_tg').innerText = this.value + '.0 °C'">
            </div>

            <div class="form-group">
                <div class="slider-row">
                    <label>Target Tensile Strength (MPa):</label>
                    <span id="lbl_target_tensile" class="slider-val">75.0 MPa</span>
                </div>
                <input type="range" id="slider_tensile" min="10" max="150" value="75" oninput="document.getElementById('lbl_target_tensile').innerText = this.value + '.0 MPa'">
            </div>

            <div class="form-group">
                <div class="slider-row">
                    <label>Target Elastic Modulus (GPa):</label>
                    <span id="lbl_target_modulus" class="slider-val">3.0 GPa</span>
                </div>
                <input type="range" id="slider_modulus" min="1" max="8" value="3" oninput="document.getElementById('lbl_target_modulus').innerText = this.value + '.0 GPa'">
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px;">
                <div>
                    <div class="slider-row">
                        <label>Max SA Score (Threshold):</label>
                        <span id="lbl_target_sa" class="slider-val">4.5</span>
                    </div>
                    <input type="range" id="slider_sa" min="1" max="10" step="0.5" value="4.5" oninput="document.getElementById('lbl_target_sa').innerText = this.value">
                </div>
                <div>
                    <label style="display:block; font-size:13px; font-weight:600; color:var(--text-muted); margin-bottom:6px;">Batch Size:</label>
                    <select id="batch_size_select">
                        <option value="5">5 Candidates</option>
                        <option value="10" selected>10 Candidates</option>
                        <option value="20">20 Candidates</option>
                        <option value="50">50 Candidates</option>
                    </select>
                </div>
            </div>

            <button class="btn-primary btn-emerald" onclick="runInverseGeneration()">Generate Polymer Candidates</button>

            <div id="batch_results_area" style="margin-top:16px; display:none;">
                <h4 style="font-size:14px; margin-bottom:8px; color:var(--accent-cyan);">Generated Candidates Pool (Click row to view):</h4>
                <div class="table-wrap">
                    <table id="batch_table">
                        <thead>
                            <tr><th>Rank</th><th>Canonical SMILES</th><th>SA Score</th><th>Pred Tg</th><th>Delta</th></tr>
                        </thead>
                        <tbody id="batch_table_body"></tbody>
                    </table>
                </div>
                <div class="btn-group">
                    <button class="btn-secondary" onclick="exportBatchCSV()">Export Batch (CSV)</button>
                    <button class="btn-secondary" onclick="exportBatchSDF()">Export Batch (SDF)</button>
                </div>
            </div>
        </div>

        <!-- Tab 3: History & Database -->
        <div id="tab-history" class="card tab-content" style="display:none;">
            <h3 style="margin-bottom:8px; font-size:16px;">SQLite Database History Log</h3>
            <div class="form-group" style="margin-top:12px;">
                <input type="text" id="history_search" placeholder="Search by SMILES, Tg, or Molecule ID..." oninput="filterHistory()">
            </div>
            <div class="table-wrap">
                <table id="history_table">
                    <thead>
                        <tr><th>ID</th><th>Canonical SMILES</th><th>SA Score</th><th>Predictions</th></tr>
                    </thead>
                    <tbody id="history_table_body"></tbody>
                </table>
            </div>
            <div class="btn-group">
                <a href="/api/export/csv" class="btn-secondary" style="text-align:center; text-decoration:none;">Download History CSV</a>
                <a href="/api/export/sdf" class="btn-secondary" style="text-align:center; text-decoration:none;">Download History SDF</a>
            </div>
        </div>
    </div>

    <!-- Right Panel: 2D Skeletal Visualizer & Property Metrics -->
    <div class="panel-right">
        <div class="card">
            <h3 style="margin-bottom:12px; font-size:15px; color:var(--accent-cyan);">2D Molecular Skeletal Structure</h3>
            <div id="viewport" class="viewport-box">
                <span style="color:var(--text-muted); font-weight:600;">No Molecular Structure Active<br>(Run Prediction or Generation Pipeline)</span>
            </div>
        </div>

        <div class="card">
            <h3 style="margin-bottom:12px; font-size:15px; color:var(--accent-cyan);">Predicted Metrics & Feasibility</h3>
            <div class="metrics-grid">
                <div class="metric-card wide">
                    <div class="metric-title">Synthetic Accessibility (SA) Score</div>
                    <div id="metric_sa" class="metric-val" style="color:var(--accent-emerald);">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Glass Transition (Tg)</div>
                    <div id="metric_tg" class="metric-val">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Polymer Density</div>
                    <div id="metric_density" class="metric-val">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Tensile Strength</div>
                    <div id="metric_tensile" class="metric-val">--</div>
                </div>
                <div class="metric-card">
                    <div class="metric-title">Elastic Modulus</div>
                    <div id="metric_modulus" class="metric-val">--</div>
                </div>
            </div>
            <button id="btn_save" class="btn-primary" style="margin-top:16px; background:#6366f1;" onclick="saveCurrentRecord()" disabled>
                Save Record to SQLite Database
            </button>
        </div>
    </div>
</div>

<div class="status-footer">
    <span id="status_text">Status: Ready. Connected to SQLite Database & RDKit Engine.</span>
    <span>Polymer Informatics Core v1.0</span>
</div>

<script>
    let currentResult = null;
    let currentBatch = [];
    let historyRecords = [];

    function switchTab(tabId) {
        document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
        document.querySelectorAll('.tabs-header .tab-btn').forEach(el => el.classList.remove('active'));
        document.getElementById(tabId).style.display = 'block';
        event.target.classList.add('active');

        if (tabId === 'tab-history') {
            fetchHistory();
        }
    }

    function setSmiles(s) {
        document.getElementById('smiles_input').value = s;
    }

    async function runForwardPrediction() {
        const smiles = document.getElementById('smiles_input').value.trim();
        if (!smiles) { alert('Please enter a SMILES string.'); return; }

        updateStatus('Validating structure & predicting QSPR properties...');
        try {
            const res = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ smiles })
            });
            const data = await res.json();
            if (!res.ok) {
                alert('Validation Error: ' + (data.detail?.error_message || 'Invalid structure'));
                updateStatus('Validation failed.');
                return;
            }

            renderResult(data);
            updateStatus('Structure processed successfully.');
        } catch (e) {
            alert('Request error: ' + e.message);
            updateStatus('Error occurred.');
        }
    }

    async function runInverseGeneration() {
        const tg = parseFloat(document.getElementById('slider_tg').value);
        const tensile = parseFloat(document.getElementById('slider_tensile').value);
        const modulus = parseFloat(document.getElementById('slider_modulus').value);
        const sa = parseFloat(document.getElementById('slider_sa').value);
        const batchSize = parseInt(document.getElementById('batch_size_select').value);

        updateStatus('Generating & filtering polymer candidate batch...');
        try {
            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_tg: tg,
                    target_tensile: tensile,
                    target_elasticity: modulus,
                    max_sa_score: sa,
                    batch_size: batchSize
                })
            });
            const data = await res.json();
            if (!res.ok) {
                alert('Generation Error: ' + (data.detail || 'Could not generate candidates.'));
                updateStatus('Generation failed.');
                return;
            }

            currentBatch = data.candidates;
            displayBatch(data.candidates);
            if (data.candidates.length > 0) {
                renderResult(data.candidates[0]);
            }
            updateStatus(`Generated ${data.candidates.length} viable candidate(s).`);
        } catch (e) {
            alert('Generation error: ' + e.message);
            updateStatus('Error occurred.');
        }
    }

    function displayBatch(candidates) {
        const area = document.getElementById('batch_results_area');
        const tbody = document.getElementById('batch_table_body');
        tbody.innerHTML = '';
        area.style.display = 'block';

        candidates.forEach((c, idx) => {
            const tr = document.createElement('tr');
            const err = Math.round((c.total_error || 0) * 1000) / 10;
            tr.innerHTML = `
                <td>#${idx + 1}</td>
                <td>${c.canonical_smiles}</td>
                <td>${c.sa_score}</td>
                <td>${c.tg} °C</td>
                <td>${err}% delta</td>
            `;
            tr.onclick = () => renderResult(c);
            tbody.appendChild(tr);
        });
    }

    function renderResult(res) {
        currentResult = res;
        document.getElementById('btn_save').disabled = false;

        // Metrics
        const sa = res.sa_score;
        const saBadge = sa <= 4.5 ? 'Synthesizable' : 'Complex';
        document.getElementById('metric_sa').innerHTML = `${sa} <span style="font-size:12px; font-weight:normal;">(${saBadge})</span>`;
        document.getElementById('metric_tg').innerText = `${res.tg} °C`;
        document.getElementById('metric_density').innerText = `${res.density} g/cm³`;
        document.getElementById('metric_tensile').innerText = `${res.tensile_strength} MPa`;
        document.getElementById('metric_modulus').innerText = `${res.elasticity} GPa`;

        // 2D Viewport Image
        const vp = document.getElementById('viewport');
        if (res.image_base64) {
            vp.innerHTML = `<img src="data:image/png;base64,${res.image_base64}" alt="2D Molecular Structure">`;
            vp.style.border = '2px solid #0284c7';
        } else {
            vp.innerHTML = `<span style="font-family:'JetBrains Mono',monospace; font-weight:bold; color:var(--accent-emerald);">Canonical SMILES:<br>${res.canonical_smiles}</span>`;
            vp.style.border = '2px solid #10b981';
        }

        // Descriptors in Forward Tab
        const descBox = document.getElementById('desc_box');
        if (res.molecular_formula) {
            descBox.innerHTML = `<b>Formula:</b> ${res.molecular_formula} | <b>MW:</b> ${res.molecular_weight} g/mol | <b>LogP:</b> ${res.logp} | <b>TPSA:</b> ${res.tpsa} Å²`;
        }
    }

    async function saveCurrentRecord() {
        if (!currentResult) return;
        try {
            const res = await fetch('/api/history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    smiles_string: currentResult.raw_smiles || currentResult.canonical_smiles,
                    canonical_smiles: currentResult.canonical_smiles,
                    sa_score: currentResult.sa_score,
                    predictions: currentResult.predictions || []
                })
            });
            if (res.ok) {
                alert('Saved molecule successfully to SQLite database!');
                document.getElementById('btn_save').disabled = true;
            }
        } catch (e) {
            alert('Save error: ' + e.message);
        }
    }

    async function fetchHistory() {
        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            historyRecords = data.records;
            populateHistoryTable(historyRecords);
        } catch (e) {
            console.error(e);
        }
    }

    function populateHistoryTable(records) {
        const tbody = document.getElementById('history_table_body');
        tbody.innerHTML = '';
        records.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${r.molecule_id}</td>
                <td>${r.canonical_smiles}</td>
                <td>${r.sa_score ?? 'N/A'}</td>
                <td>${r.predictions ?? 'N/A'}</td>
            `;
            tr.onclick = () => {
                document.getElementById('smiles_input').value = r.canonical_smiles;
                switchTab('tab-forward');
                runForwardPrediction();
            };
            tbody.appendChild(tr);
        });
    }

    function filterHistory() {
        const q = document.getElementById('history_search').value.toLowerCase();
        const filtered = historyRecords.filter(r => 
            String(r.canonical_smiles).toLowerCase().includes(q) ||
            String(r.predictions).toLowerCase().includes(q) ||
            String(r.molecule_id).includes(q)
        );
        populateHistoryTable(filtered);
    }

    function updateStatus(msg) {
        document.getElementById('status_text').innerText = 'Status: ' + msg;
    }
</script>

</body>
</html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
