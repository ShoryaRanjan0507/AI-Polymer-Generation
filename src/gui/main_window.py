import sys
import os
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QTabWidget, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QProgressBar, QFrame, 
    QTableWidget, QTableWidgetItem, QHeaderView, QSlider,
    QMessageBox, QGroupBox, QFileDialog, QComboBox, QSplitter
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QColor, QIcon, QImage

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.database.database_manager import DatabaseManager
from src.gui.workers import PipelineWorker
from src.backend.validator import validate_and_process_smiles
from src.backend.exporter import export_to_csv, export_to_sdf


class PolymerAppHomepage(QMainWindow):
    """
    Main Desktop Interface for Polymer Property Prediction & Generation Platform.
    Complies fully with PRD requirements:
    - 2D skeletal molecular rendering on-screen
    - Forward QSPR property prediction & chemical validation (RDKit)
    - Inverse multi-property AI generation with batch ranking & SA thresholding
    - Searchable database history with CSV & SDF export
    - Dark & Light high-contrast theme support
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Polymer Informatics & Generative Design Platform")
        self.resize(1280, 800)
        self.db = DatabaseManager("polymer_data.db")
        self.current_result: Optional[Dict[str, Any]] = None
        self.current_batch: List[Dict[str, Any]] = []
        self.is_dark_mode = True

        self.assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets"))
        self.sun_icon_path = os.path.join(self.assets_dir, "sun.svg")
        self.moon_icon_path = os.path.join(self.assets_dir, "moon.svg")

        self._init_ui()
        self.apply_theme()
        self.refresh_history_table()

    def get_dark_stylesheet(self) -> str:
        return """
            QMainWindow { background-color: #0f172a; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #f8fafc; font-size: 13px; }
            QTabWidget::pane { border: 1px solid #334155; background: #1e293b; border-radius: 8px; }
            QTabBar::tab { background: #0f172a; color: #94a3b8; padding: 10px 18px; border: 1px solid #334155; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; }
            QTabBar::tab:selected { background: #1e293b; color: #38bdf8; border-top: 2px solid #38bdf8; }
            QGroupBox { border: 1px solid #334155; border-radius: 8px; margin-top: 14px; font-weight: bold; color: #cbd5e1; padding-top: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #38bdf8; font-size: 13px; }
            QLineEdit, QComboBox { background-color: #0b1120; border: 1px solid #475569; color: #f8fafc; padding: 8px 10px; border-radius: 6px; font-size: 13px; }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #38bdf8; }
            QLabel { color: #e2e8f0; }
            QMessageBox { background-color: #1e293b; color: #f8fafc; }
            QMessageBox QLabel { color: #f8fafc; }
            QMessageBox QPushButton { background-color: #0284c7; color: #ffffff; border-radius: 4px; padding: 6px 16px; font-weight: bold; min-width: 60px; }
            QMessageBox QPushButton:hover { background-color: #0369a1; }
        """

    def get_light_stylesheet(self) -> str:
        return """
            QMainWindow { background-color: #f1f5f9; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #0f172a; font-size: 13px; }
            QTabWidget::pane { border: 1px solid #cbd5e1; background: #ffffff; border-radius: 8px; }
            QTabBar::tab { background: #e2e8f0; color: #475569; padding: 10px 18px; border: 1px solid #cbd5e1; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; }
            QTabBar::tab:selected { background: #ffffff; color: #0284c7; border-top: 2px solid #0284c7; }
            QGroupBox { border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 14px; font-weight: bold; color: #334155; padding-top: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #0284c7; font-size: 13px; }
            QLineEdit, QComboBox { background-color: #f8fafc; border: 1px solid #94a3b8; color: #0f172a; padding: 8px 10px; border-radius: 6px; font-size: 13px; }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #0284c7; }
            QLabel { color: #1e293b; }
            QMessageBox { background-color: #ffffff; color: #0f172a; }
            QMessageBox QLabel { color: #0f172a; }
            QMessageBox QPushButton { background-color: #0284c7; color: #ffffff; border-radius: 4px; padding: 6px 16px; font-weight: bold; min-width: 60px; }
            QMessageBox QPushButton:hover { background-color: #0369a1; }
        """

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # 1. Header Toolbar
        self.header_frame = QFrame()
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(14, 10, 14, 10)

        self.title_label = QLabel("AI Polymer Generation & Property Prediction Platform")
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.btn_theme_toggle = QPushButton()
        self.btn_theme_toggle.setFixedSize(38, 38)
        self.btn_theme_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme_toggle.setToolTip("Toggle Light/Dark Theme")
        self.btn_theme_toggle.setIconSize(QSize(20, 20))
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.btn_theme_toggle)

        main_layout.addWidget(self.header_frame)

        # 2. Main Split Area
        workspace_layout = QHBoxLayout()
        workspace_layout.setSpacing(14)

        # Left Column: Tabs
        self.tabs = QTabWidget()
        self.tab_forward = QWidget()
        self.tab_inverse = QWidget()
        self.tab_history = QWidget()

        self.tabs.addTab(self.tab_forward, "Forward Prediction")
        self.tabs.addTab(self.tab_inverse, "Inverse AI Design")
        self.tabs.addTab(self.tab_history, "Database & History")

        self._setup_forward_tab()
        self._setup_inverse_tab()
        self._setup_history_tab()

        workspace_layout.addWidget(self.tabs, stretch=6)

        # Right Column: 2D Visualizer & Dashboard Cards
        right_panel = self._build_visualization_panel()
        workspace_layout.addLayout(right_panel, stretch=4)

        main_layout.addLayout(workspace_layout)

        # 3. Bottom Status Bar
        self.bottom_frame = QFrame()
        bottom_layout = QVBoxLayout(self.bottom_frame)
        bottom_layout.setSpacing(4)
        bottom_layout.setContentsMargins(10, 8, 10, 8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.status_log = QLabel("Status: System Ready. SQLite Engine & RDKit Pipeline Connected.")
        self.status_log.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addWidget(self.status_log)
        main_layout.addWidget(self.bottom_frame)

    def _setup_forward_tab(self):
        layout = QVBoxLayout(self.tab_forward)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.info_box_forward = QLabel(
            "Input a monomer or polymer repeat unit SMILES representation. "
            "The pipe-and-filter engine validates chemical valence, computes SA score, "
            "and forward-predicts thermal & mechanical properties."
        )
        self.info_box_forward.setWordWrap(True)
        layout.addWidget(self.info_box_forward)

        # SMILES Input Field
        lbl_smiles = QLabel("Monomer SMILES String:")
        lbl_smiles.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(lbl_smiles)

        self.smiles_input = QLineEdit()
        self.smiles_input.setPlaceholderText("e.g., CC(=C)C(=O)Oc1ccccc1 (Phenyl methacrylate)")
        self.smiles_input.setText("CC(=C)C(=O)Oc1ccccc1")
        layout.addWidget(self.smiles_input)

        # Quick Examples Buttons
        example_layout = QHBoxLayout()
        example_layout.addWidget(QLabel("Quick Examples:"))
        for name, sm in [
            ("Kapton Precursor", "O=C1NC(=O)c2ccc(Oc3ccc4c(c3)C(=O)NC4=O)cc21"),
            ("MMA", "CC(=C)C(=O)OC"),
            ("Butyl Acrylate", "C=CC(=O)OCCCC"),
            ("Bisphenol-A", "CC(C)(c1ccc(O)cc1)c2ccc(O)cc2")
        ]:
            btn_ex = QPushButton(name)
            btn_ex.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_ex.clicked.connect(lambda checked, s=sm: self.smiles_input.setText(s))
            example_layout.addWidget(btn_ex)
        example_layout.addStretch()
        layout.addLayout(example_layout)

        # Validate Button
        self.btn_predict = QPushButton("Validate Structure && Predict Properties")
        self.btn_predict.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_predict.clicked.connect(self.run_forward_prediction)
        layout.addWidget(self.btn_predict)

        # Chemical Descriptors Summary Box
        self.group_descriptors = QGroupBox("Molecular Descriptors")
        desc_layout = QVBoxLayout(self.group_descriptors)
        self.lbl_descriptors = QLabel("Run validation to compute formula, MW, LogP, and TPSA.")
        self.lbl_descriptors.setWordWrap(True)
        desc_layout.addWidget(self.lbl_descriptors)
        layout.addWidget(self.group_descriptors)

        layout.addStretch()

    def _setup_inverse_tab(self):
        layout = QVBoxLayout(self.tab_inverse)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.info_box_inverse = QLabel(
            "Specify target thermomechanical constraints. The generative model will synthesize "
            "candidate monomers, filter unviable chemistry, and rank by property matching."
        )
        self.info_box_inverse.setWordWrap(True)
        layout.addWidget(self.info_box_inverse)

        # Target Parameters Box
        self.group_box_params = QGroupBox("Target Physical Constraints")
        param_layout = QVBoxLayout(self.group_box_params)
        param_layout.setSpacing(10)

        # 1. Target Tg
        tg_header = QHBoxLayout()
        tg_header.addWidget(QLabel("Target Glass Transition Temp (Tg, °C):"))
        self.lbl_target_tg = QLabel("180.0 °C")
        self.lbl_target_tg.setStyleSheet("background-color: #0284c7; color: #ffffff; padding: 2px 8px; border-radius: 4px; font-weight: bold;")
        tg_header.addStretch()
        tg_header.addWidget(self.lbl_target_tg)
        param_layout.addLayout(tg_header)

        self.slider_tg = QSlider(Qt.Orientation.Horizontal)
        self.slider_tg.setRange(-50, 300)
        self.slider_tg.setValue(180)
        self.slider_tg.valueChanged.connect(lambda v: self.lbl_target_tg.setText(f"{v}.0 °C"))
        param_layout.addWidget(self.slider_tg)

        # 2. Target Tensile Strength
        tensile_header = QHBoxLayout()
        tensile_header.addWidget(QLabel("Target Tensile Strength (MPa):"))
        self.lbl_target_tensile = QLabel("75.0 MPa")
        self.lbl_target_tensile.setStyleSheet("background-color: #0284c7; color: #ffffff; padding: 2px 8px; border-radius: 4px; font-weight: bold;")
        tensile_header.addStretch()
        tensile_header.addWidget(self.lbl_target_tensile)
        param_layout.addLayout(tensile_header)

        self.slider_tensile = QSlider(Qt.Orientation.Horizontal)
        self.slider_tensile.setRange(10, 150)
        self.slider_tensile.setValue(75)
        self.slider_tensile.valueChanged.connect(lambda v: self.lbl_target_tensile.setText(f"{v}.0 MPa"))
        param_layout.addWidget(self.slider_tensile)

        # 3. Target Elastic Modulus
        mod_header = QHBoxLayout()
        mod_header.addWidget(QLabel("Target Elastic Modulus (GPa):"))
        self.lbl_target_modulus = QLabel("3.0 GPa")
        self.lbl_target_modulus.setStyleSheet("background-color: #0284c7; color: #ffffff; padding: 2px 8px; border-radius: 4px; font-weight: bold;")
        mod_header.addStretch()
        mod_header.addWidget(self.lbl_target_modulus)
        param_layout.addLayout(mod_header)

        self.slider_modulus = QSlider(Qt.Orientation.Horizontal)
        self.slider_modulus.setRange(1, 8)
        self.slider_modulus.setValue(3)
        self.slider_modulus.valueChanged.connect(lambda v: self.lbl_target_modulus.setText(f"{v}.0 GPa"))
        param_layout.addWidget(self.slider_modulus)

        # 4. SA Threshold & Batch Size Controls
        control_row = QHBoxLayout()
        control_row.addWidget(QLabel("Max Acceptable SA Score:"))
        self.sa_slider = QSlider(Qt.Orientation.Horizontal)
        self.sa_slider.setRange(1, 10)
        self.sa_slider.setValue(4)
        self.lbl_sa_val = QLabel("4.0 (Moderate)")
        self.lbl_sa_val.setStyleSheet("background-color: #0284c7; color: #ffffff; padding: 2px 8px; border-radius: 4px; font-weight: bold;")
        self.sa_slider.valueChanged.connect(self.update_sa_slider_label)
        control_row.addWidget(self.sa_slider)
        control_row.addWidget(self.lbl_sa_val)

        control_row.addSpacing(16)
        control_row.addWidget(QLabel("Batch Size:"))
        self.combo_batch_size = QComboBox()
        self.combo_batch_size.addItems(["5", "10", "20", "50"])
        self.combo_batch_size.setCurrentText("10")
        control_row.addWidget(self.combo_batch_size)

        param_layout.addLayout(control_row)
        layout.addWidget(self.group_box_params)

        # Generate Button
        self.btn_generate = QPushButton("Generate Polymer Monomer Candidates")
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.clicked.connect(self.run_inverse_generation)
        layout.addWidget(self.btn_generate)

        # Batch Results Table
        self.lbl_batch_header = QLabel("Generated Candidates Pool (Click row to inspect 2D structure):")
        self.lbl_batch_header.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(self.lbl_batch_header)

        self.batch_table = QTableWidget()
        self.batch_table.setColumnCount(5)
        self.batch_table.setHorizontalHeaderLabels(["Rank", "Canonical SMILES", "SA Score", "Pred Tg", "Error Match"])
        self.batch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.batch_table.horizontalHeader().setStretchLastSection(True)
        self.batch_table.setColumnWidth(0, 50)
        self.batch_table.setColumnWidth(1, 180)
        self.batch_table.setColumnWidth(2, 75)
        self.batch_table.setColumnWidth(3, 85)
        self.batch_table.cellClicked.connect(self.on_batch_row_selected)
        layout.addWidget(self.batch_table)

        # Batch Actions (Export CSV / SDF)
        batch_actions = QHBoxLayout()
        self.btn_export_batch_csv = QPushButton("Export Batch (CSV)")
        self.btn_export_batch_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_batch_csv.clicked.connect(self.export_batch_csv)
        batch_actions.addWidget(self.btn_export_batch_csv)

        self.btn_export_batch_sdf = QPushButton("Export Batch (SDF)")
        self.btn_export_batch_sdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_batch_sdf.clicked.connect(self.export_batch_sdf)
        batch_actions.addWidget(self.btn_export_batch_sdf)

        layout.addLayout(batch_actions)

    def update_sa_slider_label(self, value: int):
        status_text = "Easy" if value <= 3 else ("Moderate" if value <= 6 else "Complex")
        self.lbl_sa_val.setText(f"{value}.0 ({status_text})")

    def _setup_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Search Bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search / Filter Records:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by SMILES or properties...")
        self.search_input.textChanged.connect(self.filter_history_table)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # History Table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["ID", "Canonical SMILES", "SA Score", "Predicted Properties"])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        self.history_table.setColumnWidth(0, 50)
        self.history_table.setColumnWidth(1, 200)
        self.history_table.setColumnWidth(2, 85)
        self.history_table.setSortingEnabled(True)
        self.history_table.setWordWrap(True)
        self.history_table.cellClicked.connect(self.on_history_row_selected)
        layout.addWidget(self.history_table)

        # History Action Bar
        action_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh Database")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.refresh_history_table)
        action_layout.addWidget(self.btn_refresh)

        self.btn_export_hist_csv = QPushButton("Export All to CSV")
        self.btn_export_hist_csv.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_hist_csv.clicked.connect(self.export_history_csv)
        action_layout.addWidget(self.btn_export_hist_csv)

        self.btn_export_hist_sdf = QPushButton("Export All to SDF")
        self.btn_export_hist_sdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export_hist_sdf.clicked.connect(self.export_history_sdf)
        action_layout.addWidget(self.btn_export_hist_sdf)

        layout.addLayout(action_layout)

    def _build_visualization_panel(self) -> QVBoxLayout:
        panel = QVBoxLayout()
        panel.setContentsMargins(0, 0, 0, 0)
        panel.setSpacing(10)

        # 2D Structure Viewport
        self.viewport_group = QGroupBox("2D Skeletal Molecular Structure")
        viewport_layout = QVBoxLayout(self.viewport_group)

        self.image_viewport = QLabel("No Structure Active\n(Run Forward or Inverse Pipeline)")
        self.image_viewport.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_viewport.setMinimumHeight(240)
        viewport_layout.addWidget(self.image_viewport)

        panel.addWidget(self.viewport_group)

        # Property Dashboard Cards
        self.dashboard_group = QGroupBox("Predicted Metrics && Laboratory Feasibility")
        dash_layout = QVBoxLayout(self.dashboard_group)
        dash_layout.setSpacing(8)

        self.lbl_sa_score = QLabel()
        dash_layout.addWidget(self.lbl_sa_score)

        self.lbl_tg = QLabel()
        dash_layout.addWidget(self.lbl_tg)

        self.lbl_density = QLabel()
        dash_layout.addWidget(self.lbl_density)

        self.lbl_tensile = QLabel()
        dash_layout.addWidget(self.lbl_tensile)

        self.lbl_modulus = QLabel()
        dash_layout.addWidget(self.lbl_modulus)

        panel.addWidget(self.dashboard_group)

        # Action Button: Save to DB
        self.btn_save_db = QPushButton("Save Record to SQLite Database")
        self.btn_save_db.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_db.clicked.connect(self.save_current_to_db)
        panel.addWidget(self.btn_save_db)

        return panel

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        if self.current_result:
            # Re-render 2D structure bytes with the new theme palette
            smiles = self.current_result.get("canonical_smiles") or self.current_result.get("raw_smiles")
            if smiles:
                reprocessed = validate_and_process_smiles(smiles, is_dark_mode=self.is_dark_mode)
                self.current_result["image_bytes"] = reprocessed.get("image_bytes")
            self.update_result_ui(self.current_result)
        else:
            self.update_empty_dashboard()

    def apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet(self.get_dark_stylesheet())
            self.header_frame.setStyleSheet("background-color: #0b1120; border: 1px solid #334155; border-radius: 8px;")
            self.title_label.setStyleSheet("color: #f8fafc;")
            self.btn_theme_toggle.setIcon(QIcon(self.sun_icon_path))
            self.btn_theme_toggle.setStyleSheet("""
                QPushButton { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; }
                QPushButton:hover { background-color: #334155; border-color: #38bdf8; }
            """)
            self.bottom_frame.setStyleSheet("background: #0b1120; border: 1px solid #334155; border-radius: 6px;")
            self.progress_bar.setStyleSheet("""
                QProgressBar { height: 10px; border-radius: 5px; text-align: center; background-color: #1e293b; color: transparent; }
                QProgressBar::chunk { background-color: #0284c7; border-radius: 5px; }
            """)
            self.status_log.setStyleSheet("color: #94a3b8;")
            self.btn_predict.setStyleSheet("""
                QPushButton { background-color: #0284c7; color: #ffffff; padding: 10px; font-size: 14px; font-weight: bold; border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #0369a1; }
                QPushButton:disabled { background-color: #334155; color: #64748b; }
            """)
            self.btn_generate.setStyleSheet("""
                QPushButton { background-color: #16a34a; color: #ffffff; padding: 10px; font-size: 14px; font-weight: bold; border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #15803d; }
                QPushButton:disabled { background-color: #334155; color: #64748b; }
            """)
            self.btn_save_db.setStyleSheet("""
                QPushButton { background-color: #6366f1; color: #ffffff; padding: 10px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px; }
                QPushButton:hover { background-color: #4f46e5; }
            """)
            self.history_table.setStyleSheet("""
                QTableWidget { background-color: #0b1120; color: #f8fafc; gridline-color: #334155; border: 1px solid #334155; border-radius: 6px; }
                QHeaderView::section { background-color: #1e293b; color: #38bdf8; font-weight: bold; border: 1px solid #334155; padding: 6px; }
            """)
            self.batch_table.setStyleSheet("""
                QTableWidget { background-color: #0b1120; color: #f8fafc; gridline-color: #334155; border: 1px solid #334155; border-radius: 6px; }
                QHeaderView::section { background-color: #1e293b; color: #38bdf8; font-weight: bold; border: 1px solid #334155; padding: 6px; }
            """)
            if not self.current_result:
                self.image_viewport.setStyleSheet("border: 2px dashed #475569; background: #0b1120; min-height: 240px; font-weight: bold; color: #94a3b8; border-radius: 6px;")
        else:
            self.setStyleSheet(self.get_light_stylesheet())
            self.header_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px;")
            self.title_label.setStyleSheet("color: #0f172a;")
            self.btn_theme_toggle.setIcon(QIcon(self.moon_icon_path))
            self.btn_theme_toggle.setStyleSheet("""
                QPushButton { background-color: #e2e8f0; border: 1px solid #cbd5e1; border-radius: 8px; }
                QPushButton:hover { background-color: #cbd5e1; border-color: #0284c7; }
            """)
            self.bottom_frame.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px;")
            self.progress_bar.setStyleSheet("""
                QProgressBar { height: 10px; border-radius: 5px; text-align: center; background-color: #e2e8f0; color: transparent; }
                QProgressBar::chunk { background-color: #0284c7; border-radius: 5px; }
            """)
            self.status_log.setStyleSheet("color: #475569;")
            self.btn_predict.setStyleSheet("""
                QPushButton { background-color: #0284c7; color: #ffffff; padding: 10px; font-size: 14px; font-weight: bold; border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #0369a1; }
                QPushButton:disabled { background-color: #cbd5e1; color: #94a3b8; }
            """)
            self.btn_generate.setStyleSheet("""
                QPushButton { background-color: #16a34a; color: #ffffff; padding: 10px; font-size: 14px; font-weight: bold; border-radius: 6px; border: none; }
                QPushButton:hover { background-color: #15803d; }
                QPushButton:disabled { background-color: #cbd5e1; color: #94a3b8; }
            """)
            self.btn_save_db.setStyleSheet("""
                QPushButton { background-color: #4f46e5; color: #ffffff; padding: 10px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px; }
                QPushButton:hover { background-color: #4338ca; }
            """)
            self.history_table.setStyleSheet("""
                QTableWidget { background-color: #ffffff; color: #0f172a; gridline-color: #cbd5e1; border: 1px solid #cbd5e1; border-radius: 6px; }
                QHeaderView::section { background-color: #e2e8f0; color: #0284c7; font-weight: bold; border: 1px solid #cbd5e1; padding: 6px; }
            """)
            self.batch_table.setStyleSheet("""
                QTableWidget { background-color: #ffffff; color: #0f172a; gridline-color: #cbd5e1; border: 1px solid #cbd5e1; border-radius: 6px; }
                QHeaderView::section { background-color: #e2e8f0; color: #0284c7; font-weight: bold; border: 1px solid #cbd5e1; padding: 6px; }
            """)
            if not self.current_result:
                self.image_viewport.setStyleSheet("border: 2px dashed #94a3b8; background: #ffffff; min-height: 240px; font-weight: bold; color: #64748b; border-radius: 6px;")

        if not self.current_result:
            self.update_empty_dashboard()

    def update_empty_dashboard(self):
        title_color = "#94a3b8" if self.is_dark_mode else "#64748b"
        val_color = "#38bdf8" if self.is_dark_mode else "#0284c7"
        bg_color = "#0b1120" if self.is_dark_mode else "#ffffff"
        border_color = "#334155" if self.is_dark_mode else "#cbd5e1"
        card_style = f"background: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 6px;"

        self.lbl_sa_score.setText(f"<div style='text-align: center;'><span style='font-size: 11px; color: {title_color};'>Synthetic Accessibility (SA) Score</span><br/><span style='font-size: 16px; color: {val_color}; font-weight: bold;'>--</span></div>")
        self.lbl_sa_score.setStyleSheet(card_style)

        self.lbl_tg.setText(f"<div style='text-align: center;'><span style='font-size: 11px; color: {title_color};'>Glass Transition Temp (Tg)</span><br/><span style='font-size: 16px; color: {val_color}; font-weight: bold;'>--</span></div>")
        self.lbl_tg.setStyleSheet(card_style)

        self.lbl_density.setText(f"<div style='text-align: center;'><span style='font-size: 11px; color: {title_color};'>Polymer Density</span><br/><span style='font-size: 16px; color: {val_color}; font-weight: bold;'>--</span></div>")
        self.lbl_density.setStyleSheet(card_style)

        self.lbl_tensile.setText(f"<div style='text-align: center;'><span style='font-size: 11px; color: {title_color};'>Tensile Strength</span><br/><span style='font-size: 16px; color: {val_color}; font-weight: bold;'>--</span></div>")
        self.lbl_tensile.setStyleSheet(card_style)

        self.lbl_modulus.setText(f"<div style='text-align: center;'><span style='font-size: 11px; color: {title_color};'>Elastic Modulus</span><br/><span style='font-size: 16px; color: {val_color}; font-weight: bold;'>--</span></div>")
        self.lbl_modulus.setStyleSheet(card_style)

    def update_result_ui(self, result: dict):
        self.current_result = result
        sa = result.get("sa_score", "--")
        title_color = "#94a3b8" if self.is_dark_mode else "#64748b"
        bg_color = "#0b1120" if self.is_dark_mode else "#ffffff"
        border_color = "#334155" if self.is_dark_mode else "#cbd5e1"
        card_style = f"background: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 6px;"

        sa_val = float(sa) if isinstance(sa, (int, float)) else None
        sa_color = "#4ade80" if (sa_val is not None and sa_val <= 4.5) else "#f87171"
        sa_badge = "Synthesizable" if (sa_val is not None and sa_val <= 4.5) else "Challenging"

        self.lbl_sa_score.setText(f"<div style='text-align: center;'><span style='font-size: 11px; color: {title_color};'>Synthetic Accessibility (SA) Score</span><br/><span style='font-size: 16px; color: {sa_color}; font-weight: bold;'>{sa} ({sa_badge})</span></div>")
        self.lbl_sa_score.setStyleSheet(card_style)

        tg_val = result.get("tg", "--")
        density_val = result.get("density", "--")
        tensile_val = result.get("tensile_strength", "--")
        mod_val = result.get("elasticity", "--")

        val_color = "#38bdf8" if self.is_dark_mode else "#0284c7"
        self.lbl_tg.setText(f"<div style='text-align: center;'><span style='font-size: 11px; color: {title_color};'>Glass Transition Temp (Tg)</span><br/><span style='font-size: 16px; color: {val_color}; font-weight: bold;'>{tg_val} °C</span></div>")
        self.lbl_tg.setStyleSheet(card_style)

        self.lbl_density.setText(f"<div style='text-align: center;'><span style='font-size: 11px; color: {title_color};'>Polymer Density</span><br/><span style='font-size: 16px; color: {val_color}; font-weight: bold;'>{density_val} g/cm³</span></div>")
        self.lbl_density.setStyleSheet(card_style)

        self.lbl_tensile.setText(f"<div style='text-align: center;'><span style='font-size: 11px; color: {title_color};'>Tensile Strength</span><br/><span style='font-size: 16px; color: {val_color}; font-weight: bold;'>{tensile_val} MPa</span></div>")
        self.lbl_tensile.setStyleSheet(card_style)

        self.lbl_modulus.setText(f"<div style='text-align: center;'><span style='font-size: 11px; color: {title_color};'>Elastic Modulus</span><br/><span style='font-size: 16px; color: {val_color}; font-weight: bold;'>{mod_val} GPa</span></div>")
        self.lbl_modulus.setStyleSheet(card_style)

        # 2D Structure Rendering to Viewport
        image_bytes = result.get("image_bytes")
        if image_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(image_bytes)
            self.image_viewport.setPixmap(pixmap.scaled(self.image_viewport.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.image_viewport.setStyleSheet(f"border: 2px solid #0284c7; background: {bg_color}; border-radius: 6px;")
        else:
            self.image_viewport.setText(f"Canonical SMILES:\n{result.get('canonical_smiles')}")
            self.image_viewport.setStyleSheet(f"border: 2px solid #10b981; background: {bg_color}; font-weight: bold; color: #10b981; border-radius: 6px;")

        # Update Molecular Descriptors in Forward Tab
        if "molecular_formula" in result:
            self.lbl_descriptors.setText(
                f"<b>Formula:</b> {result.get('molecular_formula', 'N/A')}  |  "
                f"<b>MW:</b> {result.get('molecular_weight', 'N/A')} g/mol  |  "
                f"<b>LogP:</b> {result.get('logp', 'N/A')}  |  "
                f"<b>TPSA:</b> {result.get('tpsa', 'N/A')} Å²  |  "
                f"<b>Rotatable Bonds:</b> {result.get('rotatable_bonds', 'N/A')}"
            )

    def run_forward_prediction(self):
        smiles = self.smiles_input.text().strip()
        if not smiles:
            QMessageBox.warning(self, "Input Error", "Please enter a valid SMILES string.")
            return

        self.btn_predict.setEnabled(False)
        self.progress_bar.setValue(10)
        self.status_log.setText("Pipeline: Executing forward validation worker...")

        self.worker = PipelineWorker(mode="forward", payload={"smiles": smiles}, is_dark_mode=self.is_dark_mode)
        self.worker.progress_updated.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_forward_finished)
        self.worker.error_raised.connect(self.on_worker_error)
        self.worker.start()

    def run_inverse_generation(self):
        tg_val = float(self.slider_tg.value())
        tensile_val = float(self.slider_tensile.value())
        modulus_val = float(self.slider_modulus.value())
        sa_val = float(self.sa_slider.value())
        batch_sz = int(self.combo_batch_size.currentText())

        self.btn_generate.setEnabled(False)
        self.progress_bar.setValue(10)
        self.status_log.setText("Pipeline: Running inverse candidate generation worker...")

        payload = {
            "target_tg": tg_val,
            "target_tensile": tensile_val,
            "target_elasticity": modulus_val,
            "max_sa": sa_val,
            "batch_size": batch_sz
        }

        self.worker = PipelineWorker(mode="inverse", payload=payload, is_dark_mode=self.is_dark_mode)
        self.worker.progress_updated.connect(self.on_worker_progress)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.batch_finished.connect(self.on_batch_finished)
        self.worker.error_raised.connect(self.on_worker_error)
        self.worker.start()

    def on_worker_progress(self, val: int, msg: str):
        self.progress_bar.setValue(val)
        self.status_log.setText(f"Pipeline Status ({val}%): {msg}")

    def on_forward_finished(self, result: dict):
        self.btn_predict.setEnabled(True)
        self.btn_save_db.setEnabled(True)
        self.update_result_ui(result)
        self.status_log.setText(f"Success: {result.get('message')}")

    def on_worker_finished(self, result: dict):
        self.btn_generate.setEnabled(True)
        self.btn_save_db.setEnabled(True)
        self.update_result_ui(result)
        self.status_log.setText(f"Success: {result.get('message')}")

    def on_batch_finished(self, candidates: list):
        self.current_batch = candidates
        self.batch_table.setRowCount(len(candidates))

        for idx, cand in enumerate(candidates):
            rank_item = QTableWidgetItem(f"#{idx + 1}")
            smiles_item = QTableWidgetItem(str(cand.get("canonical_smiles")))
            sa_item = QTableWidgetItem(str(cand.get("sa_score")))
            tg_item = QTableWidgetItem(f"{cand.get('tg')} °C")
            
            err = cand.get("total_error", 0.0)
            err_percent = round(err * 100.0, 1)
            err_item = QTableWidgetItem(f"{err_percent}% delta")

            self.batch_table.setItem(idx, 0, rank_item)
            self.batch_table.setItem(idx, 1, smiles_item)
            self.batch_table.setItem(idx, 2, sa_item)
            self.batch_table.setItem(idx, 3, tg_item)
            self.batch_table.setItem(idx, 4, err_item)

        self.batch_table.resizeRowsToContents()

    def on_batch_row_selected(self, row: int, col: int):
        if 0 <= row < len(self.current_batch):
            selected = self.current_batch[row]
            self.update_result_ui(selected)
            self.btn_save_db.setEnabled(True)

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

            existing_history = self.db.fetch_history(limit=500)
            existing_record = next((item for item in existing_history if item["molecule_id"] == mol_id), None)

            if existing_record and existing_record["predictions"]:
                QMessageBox.information(self, "Database Persistence", f"Molecule record (ID: {mol_id}) and predictions already saved!")
            else:
                for p in self.current_result.get("predictions", []):
                    self.db.insert_prediction(mol_id, p["name"], p["value"], p["unit"])
                QMessageBox.information(self, "Database Persistence", f"Successfully saved molecule record (ID: {mol_id}) to SQLite database!")

            self.refresh_history_table()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save record: {str(e)}")

    def refresh_history_table(self):
        records = self.db.fetch_history(limit=200)
        self.history_records = records
        self.populate_history_table(records)

    def populate_history_table(self, records: list):
        self.history_table.setSortingEnabled(False)
        self.history_table.setRowCount(len(records))

        for row_idx, r in enumerate(records):
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
        self.history_table.resizeRowsToContents()

    def filter_history_table(self, query: str):
        query = query.strip().lower()
        if not query:
            self.populate_history_table(getattr(self, "history_records", []))
            return

        filtered = [
            r for r in getattr(self, "history_records", [])
            if query in str(r.get("canonical_smiles", "")).lower()
            or query in str(r.get("predictions", "")).lower()
            or query in str(r.get("molecule_id", "")).lower()
        ]
        self.populate_history_table(filtered)

    def on_history_row_selected(self, row: int, col: int):
        smiles_item = self.history_table.item(row, 1)
        if smiles_item:
            smiles = smiles_item.text().strip()
            processed = validate_and_process_smiles(smiles, is_dark_mode=self.is_dark_mode)
            if processed["is_valid"]:
                from src.backend.predictor import PropertyPredictor
                preds = PropertyPredictor.predict_properties(processed["canonical_smiles"])
                full_res = {**processed, **preds}
                self.update_result_ui(full_res)

    def export_batch_csv(self):
        if not self.current_batch:
            QMessageBox.information(self, "Export", "No generated batch candidates available to export.")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Export Batch Candidates to CSV", "generated_polymers.csv", "CSV Files (*.csv)")
        if filepath:
            success = export_to_csv(self.current_batch, filepath)
            if success:
                QMessageBox.information(self, "Export Successful", f"Batch candidates successfully exported to:\n{filepath}")

    def export_batch_sdf(self):
        if not self.current_batch:
            QMessageBox.information(self, "Export", "No generated batch candidates available to export.")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Export Batch Candidates to SDF", "generated_polymers.sdf", "SDF Files (*.sdf)")
        if filepath:
            success = export_to_sdf(self.current_batch, filepath)
            if success:
                QMessageBox.information(self, "Export Successful", f"Batch candidates successfully exported to:\n{filepath}")

    def export_history_csv(self):
        records = self.db.fetch_history(limit=1000)
        if not records:
            QMessageBox.information(self, "Export", "No database records available to export.")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Export History to CSV", "polymer_database_history.csv", "CSV Files (*.csv)")
        if filepath:
            success = export_to_csv(records, filepath)
            if success:
                QMessageBox.information(self, "Export Successful", f"Database history successfully exported to:\n{filepath}")

    def export_history_sdf(self):
        records = self.db.fetch_history(limit=1000)
        if not records:
            QMessageBox.information(self, "Export", "No database records available to export.")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Export History to SDF", "polymer_database_history.sdf", "SDF Files (*.sdf)")
        if filepath:
            success = export_to_sdf(records, filepath)
            if success:
                QMessageBox.information(self, "Export Successful", f"Database history successfully exported to:\n{filepath}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PolymerAppHomepage()
    window.show()
    sys.exit(app.exec())
