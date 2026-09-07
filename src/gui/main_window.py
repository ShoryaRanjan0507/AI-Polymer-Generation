import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QLabel, QLineEdit, 
                            QPushButton, QTextEdit, QProgressBar, QFrame, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QSlider,
                            QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QColor

# Add src to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.database.database_manager import DatabaseManager
from src.gui.workers import MockValidationWorker

class PolymerAppHomepage(QMainWindow):
    """
    Main Desktop Interface for Polymer Property Prediction & Generation Platform.
    Integrates PyQt layout panels, asynchronous QThread workers, and SQLite persistence.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Polymer Informatics & Property Prediction Platform")
        self.resize(1150, 720)
        self.db = DatabaseManager("polymer_data.db")
        self.current_result = None

        self._init_ui()
        self.refresh_history_table()

    def _init_ui(self):
        # Set global dark theme styling for high contrast and clean UI
        self.setStyleSheet("""
            QMainWindow { background-color: #121827; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #f1f5f9; }
            QTabWidget::pane { border: 1px solid #334155; background: #1e293b; border-radius: 6px; }
            QTabBar::tab { background: #0f172a; color: #94a3b8; padding: 10px 16px; border: 1px solid #334155; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; }
            QTabBar::tab:selected { background: #1e293b; color: #38bdf8; border-top: 2px solid #38bdf8; }
            QGroupBox { border: 1px solid #334155; border-radius: 6px; margin-top: 12px; font-weight: bold; color: #cbd5e1; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #38bdf8; }
            QLineEdit { background-color: #0f172a; border: 1px solid #475569; color: #f8fafc; padding: 8px; border-radius: 4px; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #38bdf8; }
            QLabel { color: #e2e8f0; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 1. Top Title Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 10px;")
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("Polymer Property Prediction & Generation Suite")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addWidget(header_frame)


        # 2. Main Workspace Layout
        workspace_layout = QHBoxLayout()
        workspace_layout.setSpacing(12)

        # Left Column: Navigation Tabs & Forms
        self.tabs = QTabWidget()
        self.tab_forward = QWidget()
        self.tab_inverse = QWidget()
        self.tab_history = QWidget()

        self.tabs.addTab(self.tab_forward, "Forward Prediction")
        self.tabs.addTab(self.tab_inverse, "Inverse Design")
        self.tabs.addTab(self.tab_history, "Database History")

        self._setup_forward_tab()
        self._setup_inverse_tab()
        self._setup_history_tab()

        workspace_layout.addWidget(self.tabs, stretch=5)

        # Right Column: 2D Render Viewport & Property Dashboard
        right_panel = self._build_visualization_panel()
        workspace_layout.addLayout(right_panel, stretch=4)

        main_layout.addLayout(workspace_layout)

        # 3. Bottom Status Bar & Console Bar
        bottom_frame = QFrame()
        bottom_frame.setStyleSheet("background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 6px 12px;")
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setSpacing(4)
        bottom_layout.setContentsMargins(8, 8, 8, 8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar { height: 10px; border-radius: 5px; text-align: center; background-color: #1e293b; color: transparent; }
            QProgressBar::chunk { background-color: #0284c7; border-radius: 5px; }
        """)

        self.status_log = QLabel("Status: System Ready. SQLite Engine Connected.")
        self.status_log.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")

        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addWidget(self.status_log)
        main_layout.addWidget(bottom_frame)

    def _setup_forward_tab(self):
        layout = QVBoxLayout(self.tab_forward)
        layout.setContentsMargins(12, 12, 12, 12)
        
        info_box = QLabel("Input monomer SMILES representation to run RDKit validation and predict thermal/physical properties.")
        info_box.setWordWrap(True)
        info_box.setStyleSheet("color: #cbd5e1; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(info_box)

        lbl_smiles = QLabel("Monomer SMILES String:")
        lbl_smiles.setStyleSheet("color: #f1f5f9; font-weight: 600;")
        layout.addWidget(lbl_smiles)

        self.smiles_input = QLineEdit()
        self.smiles_input.setPlaceholderText("e.g., CCO, CC(=O)O, or C1=CC=CC=C1")
        layout.addWidget(self.smiles_input)

        self.btn_predict = QPushButton("Validate Structure && Predict Properties")
        self.btn_predict.setStyleSheet("""
            QPushButton { background-color: #0284c7; color: #ffffff; padding: 10px; font-size: 14px; font-weight: bold; border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #0369a1; }
            QPushButton:disabled { background-color: #334155; color: #64748b; }
        """)
        self.btn_predict.clicked.connect(self.run_forward_prediction)
        layout.addWidget(self.btn_predict)

        layout.addStretch()

    def _setup_inverse_tab(self):
        layout = QVBoxLayout(self.tab_inverse)
        layout.setContentsMargins(12, 12, 12, 12)

        info_box = QLabel("Specify target material constraints to generate candidate monomer blueprints matching criteria.")
        info_box.setWordWrap(True)
        info_box.setStyleSheet("color: #cbd5e1; font-size: 13px; margin-bottom: 8px;")
        layout.addWidget(info_box)

        group_box = QGroupBox("Target Physical Parameters")
        group_layout = QVBoxLayout(group_box)
        group_layout.setContentsMargins(12, 16, 12, 12)

        group_layout.addWidget(QLabel("Target Glass Transition Temp (Tg °C):"))
        self.tg_input = QLineEdit()
        self.tg_input.setText("180.0")
        group_layout.addWidget(self.tg_input)

        sa_header_layout = QHBoxLayout()
        lbl_sa_title = QLabel("Max Acceptable SA Score (1=Easy, 10=Hard):")
        self.lbl_sa_val = QLabel("4.0 (Moderate)")
        self.lbl_sa_val.setStyleSheet("background-color: #0284c7; color: #ffffff; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;")
        sa_header_layout.addWidget(lbl_sa_title)
        sa_header_layout.addStretch()
        sa_header_layout.addWidget(self.lbl_sa_val)
        group_layout.addLayout(sa_header_layout)

        self.sa_slider = QSlider(Qt.Orientation.Horizontal)
        self.sa_slider.setRange(1, 10)
        self.sa_slider.setValue(4)
        self.sa_slider.setStyleSheet("""
            QSlider::groove:horizontal { border: 1px solid #475569; height: 6px; background: #0f172a; border-radius: 3px; }
            QSlider::handle:horizontal { background: #38bdf8; border: 1px solid #0284c7; width: 16px; margin-top: -5px; margin-bottom: -5px; border-radius: 8px; }
        """)
        self.sa_slider.valueChanged.connect(self.update_sa_slider_label)
        group_layout.addWidget(self.sa_slider)

        layout.addWidget(group_box)

        self.btn_generate = QPushButton("Generate Monomer Candidates")
        self.btn_generate.setStyleSheet("""
            QPushButton { background-color: #16a34a; color: #ffffff; padding: 10px; font-size: 14px; font-weight: bold; border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #15803d; }
            QPushButton:disabled { background-color: #334155; color: #64748b; }
        """)
        self.btn_generate.clicked.connect(self.run_inverse_generation)
        layout.addWidget(self.btn_generate)

        layout.addStretch()

    def update_sa_slider_label(self, value: int):
        status_text = "Easy" if value <= 3 else ("Moderate" if value <= 6 else "Complex")
        self.lbl_sa_val.setText(f"{value}.0 ({status_text})")

    def _setup_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        layout.setContentsMargins(12, 12, 12, 12)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["ID", "Canonical SMILES", "SA Score", "Predicted Properties"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.setSortingEnabled(True)
        self.history_table.setWordWrap(True)
        self.history_table.setStyleSheet("""
            QTableWidget { background-color: #0f172a; color: #f8fafc; gridline-color: #334155; border: 1px solid #334155; border-radius: 6px; }
            QHeaderView::section { background-color: #1e293b; color: #38bdf8; font-weight: bold; border: 1px solid #334155; padding: 6px; }
            QHeaderView::section:hover { background-color: #334155; cursor: pointer; }
        """)
        layout.addWidget(self.history_table)

        btn_refresh = QPushButton("Refresh Database Records")
        btn_refresh.setStyleSheet("""
            QPushButton { background-color: #334155; color: #f8fafc; padding: 8px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #475569; }
        """)
        btn_refresh.clicked.connect(self.refresh_history_table)
        layout.addWidget(btn_refresh)

    def _build_visualization_panel(self):
        panel = QVBoxLayout()
        panel.setContentsMargins(0, 0, 0, 0)

        # 2D Structure Render Viewport
        viewport_group = QGroupBox("2D Structure Visualization Viewport")
        viewport_layout = QVBoxLayout(viewport_group)

        self.image_viewport = QLabel("No Structure Active\n(Run Forward or Inverse Pipeline)")
        self.image_viewport.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_viewport.setStyleSheet("border: 2px dashed #475569; background: #0f172a; min-height: 220px; font-weight: bold; color: #94a3b8; border-radius: 6px;")
        viewport_layout.addWidget(self.image_viewport)

        panel.addWidget(viewport_group)

        # Property Dashboard Cards
        dashboard_group = QGroupBox("Predicted Metrics && Feasibility")
        dash_layout = QVBoxLayout(dashboard_group)
        dash_layout.setSpacing(8)

        self.lbl_sa_score = QLabel("Synthetic Accessibility (SA) Score: --")
        self.lbl_sa_score.setStyleSheet("font-size: 13px; font-weight: bold; color: #38bdf8;")
        dash_layout.addWidget(self.lbl_sa_score)

        self.lbl_tg = QLabel("Glass Transition Temp (Tg): --")
        self.lbl_tg.setStyleSheet("font-size: 13px; font-weight: bold; color: #38bdf8;")
        dash_layout.addWidget(self.lbl_tg)

        self.lbl_density = QLabel("Density: --")
        self.lbl_density.setStyleSheet("font-size: 13px; font-weight: bold; color: #e2e8f0;")
        dash_layout.addWidget(self.lbl_density)

        panel.addWidget(dashboard_group)

        # Action Buttons
        self.btn_save_db = QPushButton("Save Record to Database")
        self.btn_save_db.setStyleSheet("""
            QPushButton { background-color: #6366f1; color: #ffffff; padding: 10px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px; }
            QPushButton:hover { background-color: #4f46e5; }
        """)
        self.btn_save_db.clicked.connect(self.save_current_to_db)
        panel.addWidget(self.btn_save_db)

        return panel

    def run_forward_prediction(self):
        smiles = self.smiles_input.text().strip()
        if not smiles:
            QMessageBox.warning(self, "Input Error", "Please enter a valid SMILES string.")
            return

        self.btn_predict.setEnabled(False)
        self.progress_bar.setValue(10)
        self.status_log.setText("Pipeline: Executing forward prediction QThread worker...")

        self.worker = MockValidationWorker(mode="forward", payload={"smiles": smiles})
        self.worker.progress_updated.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.error_raised.connect(self.on_worker_error)
        self.worker.start()

    def run_inverse_generation(self):
        try:
            tg_val = float(self.tg_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid numerical Tg value.")
            return

        self.btn_generate.setEnabled(False)
        self.progress_bar.setValue(10)
        self.status_log.setText("Pipeline: Running inverse generation QThread worker...")

        self.worker = MockValidationWorker(mode="inverse", payload={"target_tg": tg_val})
        self.worker.progress_updated.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.error_raised.connect(self.on_worker_error)
        self.worker.start()

    def on_worker_progress(self, val: int, msg: str):
        self.progress_bar.setValue(val)
        self.status_log.setText(f"Pipeline Status ({val}%): {msg}")

    def on_worker_finished(self, result: dict):
        self.btn_predict.setEnabled(True)
        self.btn_generate.setEnabled(True)
        self.current_result = result

        sa = result.get("sa_score", "--")
        self.lbl_sa_score.setText(f"Synthetic Accessibility (SA) Score: {sa} (Synthesizable)")
        self.lbl_sa_score.setStyleSheet("font-size: 13px; font-weight: bold; color: #4ade80;")

        preds = result.get("predictions", [])
        for p in preds:
            if "Glass Transition" in p["name"]:
                self.lbl_tg.setText(f"Glass Transition Temp (Tg): {p['value']} {p['unit']}")
                self.lbl_tg.setStyleSheet("font-size: 13px; font-weight: bold; color: #38bdf8;")
            elif "Density" in p["name"]:
                self.lbl_density.setText(f"Density: {p['value']} {p['unit']}")
                self.lbl_density.setStyleSheet("font-size: 13px; font-weight: bold; color: #f1f5f9;")

        self.image_viewport.setText(f"Structure Rendered\nCanonical SMILES:\n{result.get('canonical_smiles')}")
        self.image_viewport.setStyleSheet("border: 2px solid #22c55e; background: #052e16; font-weight: bold; color: #4ade80; border-radius: 6px;")
        self.status_log.setText(f"Success: {result.get('message')}")

    def on_worker_error(self, err_msg: str):
        self.btn_predict.setEnabled(True)
        self.btn_generate.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_log.setText(f"Error: {err_msg}")
        QMessageBox.critical(self, "Pipeline Error", err_msg)

    def save_current_to_db(self):
        if not self.current_result:
            QMessageBox.information(self, "Notice", "No active prediction record to save.")
            return

        try:
            raw_s = self.current_result.get("raw_smiles", self.current_result.get("canonical_smiles"))
            can_s = self.current_result.get("canonical_smiles")
            sa = self.current_result.get("sa_score")

            mol_id = self.db.insert_molecule(raw_s, can_s, sa)
            for p in self.current_result.get("predictions", []):
                self.db.insert_prediction(mol_id, p["name"], p["value"], p["unit"])

            QMessageBox.information(self, "Database Persistence", f"Successfully saved molecule record (ID: {mol_id}) to SQLite!")
            self.refresh_history_table()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save record: {str(e)}")

    def refresh_history_table(self):
        records = self.db.fetch_history()
        self.history_table.setSortingEnabled(False)
        self.history_table.setRowCount(len(records))
        
        for row_idx, r in enumerate(records):
            # Numeric ID Item for proper integer sorting (1, 2, 10 vs string 1, 10, 2)
            id_item = QTableWidgetItem()
            id_item.setData(Qt.ItemDataRole.DisplayRole, int(r["molecule_id"]))
            
            smiles_item = QTableWidgetItem(str(r["canonical_smiles"]))
            
            sa_item = QTableWidgetItem()
            if r["sa_score"] is not None:
                sa_item.setData(Qt.ItemDataRole.DisplayRole, float(r["sa_score"]))
            else:
                sa_item.setText("N/A")

            preds_item = QTableWidgetItem(str(r["predictions"] or "N/A"))

            self.history_table.setItem(row_idx, 0, id_item)
            self.history_table.setItem(row_idx, 1, smiles_item)
            self.history_table.setItem(row_idx, 2, sa_item)
            self.history_table.setItem(row_idx, 3, preds_item)

        self.history_table.setSortingEnabled(True)
        # Auto-adjust row heights to fit multi-line wrapped text
        self.history_table.resizeRowsToContents()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PolymerAppHomepage()
    window.show()
    sys.exit(app.exec())
