import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QLabel, QLineEdit, 
                            QPushButton, QTextEdit, QProgressBar, QFrame, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QSlider,
                            QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QColor, QIcon

# Add src to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.database.database_manager import DatabaseManager
from src.gui.workers import MockValidationWorker

class PolymerAppHomepage(QMainWindow):
    """
    Main Desktop Interface for Polymer Property Prediction & Generation Platform.
    Supports high-contrast Dark and Light Themes with theme-switching icon toggle.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Polymer Informatics & Property Prediction Platform")
        self.resize(1150, 720)
        self.db = DatabaseManager("polymer_data.db")
        self.current_result = None
        self.is_dark_mode = True  # Default theme mode

        self.assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets"))
        self.sun_icon_path = os.path.join(self.assets_dir, "sun.svg")
        self.moon_icon_path = os.path.join(self.assets_dir, "moon.svg")

        self._init_ui()
        self.apply_theme()
        self.refresh_history_table()

    def get_dark_stylesheet(self) -> str:
        return """
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
            QMessageBox { background-color: #1e293b; color: #f8fafc; }
            QMessageBox QLabel { color: #f8fafc; }
            QMessageBox QPushButton { background-color: #0284c7; color: #ffffff; border-radius: 4px; padding: 6px 16px; font-weight: bold; min-width: 60px; }
            QMessageBox QPushButton:hover { background-color: #0369a1; }
        """

    def get_light_stylesheet(self) -> str:
        return """
            QMainWindow { background-color: #e2e8f0; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #0f172a; }
            QTabWidget::pane { border: 1px solid #cbd5e1; background: #f1f5f9; border-radius: 6px; }
            QTabBar::tab { background: #e2e8f0; color: #475569; padding: 10px 16px; border: 1px solid #cbd5e1; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; }
            QTabBar::tab:selected { background: #f1f5f9; color: #0284c7; border-top: 2px solid #0284c7; }
            QGroupBox { border: 1px solid #cbd5e1; border-radius: 6px; margin-top: 12px; font-weight: bold; color: #334155; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #0284c7; }
            QLineEdit { background-color: #f8fafc; border: 1px solid #94a3b8; color: #0f172a; padding: 8px; border-radius: 4px; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #0284c7; }
            QLabel { color: #1e293b; }
            QMessageBox { background-color: #f1f5f9; color: #0f172a; }
            QMessageBox QLabel { color: #0f172a; }
            QMessageBox QPushButton { background-color: #0284c7; color: #ffffff; border-radius: 4px; padding: 6px 16px; font-weight: bold; min-width: 60px; }
            QMessageBox QPushButton:hover { background-color: #0369a1; }
        """



    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 1. Top Title Header with Theme Toggle Button
        self.header_frame = QFrame()
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        self.title_label = QLabel("Polymer Property Prediction & Generation")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()

        # Rounded Squircle Theme Toggle Button in Top Right
        self.btn_theme_toggle = QPushButton()
        self.btn_theme_toggle.setFixedSize(38, 38)
        self.btn_theme_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme_toggle.setToolTip("Toggle Light/Dark Theme")
        self.btn_theme_toggle.setIconSize(QSize(20, 20))
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.btn_theme_toggle)

        main_layout.addWidget(self.header_frame)

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
        self.bottom_frame = QFrame()
        bottom_layout = QVBoxLayout(self.bottom_frame)
        bottom_layout.setSpacing(4)
        bottom_layout.setContentsMargins(8, 8, 8, 8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        self.status_log = QLabel("Status: System Ready. SQLite Engine Connected.")
        self.status_log.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addWidget(self.status_log)
        main_layout.addWidget(self.bottom_frame)

    def _setup_forward_tab(self):
        layout = QVBoxLayout(self.tab_forward)
        layout.setContentsMargins(12, 12, 12, 12)
        
        self.info_box_forward = QLabel("Input monomer SMILES representation to run RDKit validation and predict thermal/physical properties.")
        self.info_box_forward.setWordWrap(True)
        layout.addWidget(self.info_box_forward)

        self.lbl_smiles = QLabel("Monomer SMILES String:")
        self.lbl_smiles.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(self.lbl_smiles)

        self.smiles_input = QLineEdit()
        self.smiles_input.setPlaceholderText("e.g., CCO, CC(=O)O, or C1=CC=CC=C1")
        layout.addWidget(self.smiles_input)

        self.btn_predict = QPushButton("Validate Structure && Predict Properties")
        self.btn_predict.clicked.connect(self.run_forward_prediction)
        layout.addWidget(self.btn_predict)

        layout.addStretch()

    def _setup_inverse_tab(self):
        layout = QVBoxLayout(self.tab_inverse)
        layout.setContentsMargins(12, 12, 12, 12)

        self.info_box_inverse = QLabel("Specify target material constraints to generate candidate monomer blueprints matching criteria.")
        self.info_box_inverse.setWordWrap(True)
        layout.addWidget(self.info_box_inverse)

        self.group_box_params = QGroupBox("Target Physical Parameters")
        group_layout = QVBoxLayout(self.group_box_params)
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
        self.sa_slider.valueChanged.connect(self.update_sa_slider_label)
        group_layout.addWidget(self.sa_slider)

        layout.addWidget(self.group_box_params)

        self.btn_generate = QPushButton("Generate Monomer Candidates")
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
        
        # User-adjustable interactive column resizing with proportional initial widths
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        self.history_table.setColumnWidth(0, 50)   # ID: compact
        self.history_table.setColumnWidth(1, 180)  # Canonical SMILES: medium
        self.history_table.setColumnWidth(2, 85)   # SA Score: compact
        # Column 3 (Predicted Properties) stretches to fill remaining space

        self.history_table.setSortingEnabled(True)
        self.history_table.setWordWrap(True)
        layout.addWidget(self.history_table)


        self.btn_refresh = QPushButton("Refresh Database Records")
        self.btn_refresh.clicked.connect(self.refresh_history_table)
        layout.addWidget(self.btn_refresh)

    def _build_visualization_panel(self):
        panel = QVBoxLayout()
        panel.setContentsMargins(0, 0, 0, 0)

        # 2D Structure Render Viewport
        self.viewport_group = QGroupBox("2D Structure Visualization Viewport")
        viewport_layout = QVBoxLayout(self.viewport_group)

        self.image_viewport = QLabel("No Structure Active\n(Run Forward or Inverse Pipeline)")
        self.image_viewport.setAlignment(Qt.AlignmentFlag.AlignCenter)
        viewport_layout.addWidget(self.image_viewport)

        panel.addWidget(self.viewport_group)

        # Property Dashboard Cards
        self.dashboard_group = QGroupBox("Predicted Metrics && Feasibility")
        dash_layout = QVBoxLayout(self.dashboard_group)
        dash_layout.setSpacing(10)
        dash_layout.setContentsMargins(12, 16, 12, 12)

        self.lbl_sa_score = QLabel()
        self.lbl_sa_score.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_layout.addWidget(self.lbl_sa_score)

        self.lbl_tg = QLabel()
        self.lbl_tg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_layout.addWidget(self.lbl_tg)

        self.lbl_density = QLabel()
        self.lbl_density.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash_layout.addWidget(self.lbl_density)

        panel.addWidget(self.dashboard_group)

        # Action Buttons
        self.btn_save_db = QPushButton("Save Record to SQLite Library")
        self.btn_save_db.clicked.connect(self.save_current_to_db)
        panel.addWidget(self.btn_save_db)

        return panel

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        if self.current_result:
            self.update_result_ui(self.current_result)
        else:
            self.update_empty_dashboard()

    def apply_theme(self):
        if self.is_dark_mode:
            self.setStyleSheet(self.get_dark_stylesheet())
            self.header_frame.setStyleSheet("background-color: #0f172a; border: 1px solid #334155; border-radius: 8px;")
            self.title_label.setStyleSheet("color: #f8fafc;")
            self.btn_theme_toggle.setIcon(QIcon(self.sun_icon_path))
            self.btn_theme_toggle.setStyleSheet("""
                QPushButton { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; }
                QPushButton:hover { background-color: #334155; border-color: #38bdf8; }
            """)
            self.bottom_frame.setStyleSheet("background: #0f172a; border: 1px solid #334155; border-radius: 6px;")
            self.progress_bar.setStyleSheet("""
                QProgressBar { height: 10px; border-radius: 5px; text-align: center; background-color: #1e293b; color: transparent; }
                QProgressBar::chunk { background-color: #0284c7; border-radius: 5px; }
            """)
            self.status_log.setStyleSheet("color: #94a3b8;")
            self.info_box_forward.setStyleSheet("color: #cbd5e1; font-size: 13px;")
            self.info_box_inverse.setStyleSheet("color: #cbd5e1; font-size: 13px;")
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
            self.sa_slider.setStyleSheet("""
                QSlider::groove:horizontal { border: 1px solid #475569; height: 6px; background: #0f172a; border-radius: 3px; }
                QSlider::handle:horizontal { background: #38bdf8; border: 1px solid #0284c7; width: 16px; margin-top: -5px; margin-bottom: -5px; border-radius: 8px; }
            """)
            self.history_table.setStyleSheet("""
                QTableWidget { background-color: #0f172a; color: #f8fafc; gridline-color: #334155; border: 1px solid #334155; border-radius: 6px; }
                QHeaderView::section { background-color: #1e293b; color: #38bdf8; font-weight: bold; border: 1px solid #334155; padding: 6px; }
            """)
            self.btn_refresh.setStyleSheet("""
                QPushButton { background-color: #334155; color: #f8fafc; padding: 8px; font-weight: bold; border-radius: 4px; border: none; }
                QPushButton:hover { background-color: #475569; }
            """)
            self.btn_save_db.setStyleSheet("""
                QPushButton { background-color: #6366f1; color: #ffffff; padding: 10px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px; }
                QPushButton:hover { background-color: #4f46e5; }
            """)
            if not self.current_result:
                self.image_viewport.setStyleSheet("border: 2px dashed #475569; background: #0f172a; min-height: 200px; font-weight: bold; color: #94a3b8; border-radius: 6px;")
        else:
            self.setStyleSheet(self.get_light_stylesheet())
            self.header_frame.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px;")
            self.title_label.setStyleSheet("color: #0f172a;")
            self.btn_theme_toggle.setIcon(QIcon(self.moon_icon_path))
            self.btn_theme_toggle.setStyleSheet("""
                QPushButton { background-color: #e2e8f0; border: 1px solid #cbd5e1; border-radius: 8px; }
                QPushButton:hover { background-color: #cbd5e1; border-color: #0284c7; }
            """)
            self.bottom_frame.setStyleSheet("background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px;")
            self.progress_bar.setStyleSheet("""
                QProgressBar { height: 10px; border-radius: 5px; text-align: center; background-color: #e2e8f0; color: transparent; }
                QProgressBar::chunk { background-color: #0284c7; border-radius: 5px; }
            """)
            self.status_log.setStyleSheet("color: #475569;")
            self.info_box_forward.setStyleSheet("color: #475569; font-size: 13px;")
            self.info_box_inverse.setStyleSheet("color: #475569; font-size: 13px;")
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
            self.sa_slider.setStyleSheet("""
                QSlider::groove:horizontal { border: 1px solid #cbd5e1; height: 6px; background: #e2e8f0; border-radius: 3px; }
                QSlider::handle:horizontal { background: #0284c7; border: 1px solid #0369a1; width: 16px; margin-top: -5px; margin-bottom: -5px; border-radius: 8px; }
            """)
            self.history_table.setStyleSheet("""
                QTableWidget { background-color: #f1f5f9; color: #0f172a; gridline-color: #cbd5e1; border: 1px solid #cbd5e1; border-radius: 6px; }
                QHeaderView::section { background-color: #e2e8f0; color: #0284c7; font-weight: bold; border: 1px solid #cbd5e1; padding: 6px; }
            """)
            self.btn_refresh.setStyleSheet("""
                QPushButton { background-color: #e2e8f0; color: #0f172a; padding: 8px; font-weight: bold; border-radius: 4px; border: 1px solid #cbd5e1; }
                QPushButton:hover { background-color: #cbd5e1; }
            """)
            self.btn_save_db.setStyleSheet("""
                QPushButton { background-color: #4f46e5; color: #ffffff; padding: 10px; font-weight: bold; border-radius: 6px; border: none; font-size: 13px; }
                QPushButton:hover { background-color: #4338ca; }
                QPushButton:disabled { background-color: #cbd5e1; color: #94a3b8; }
            """)
            if not self.current_result:
                self.image_viewport.setStyleSheet("border: 2px dashed #94a3b8; background: #f1f5f9; min-height: 200px; font-weight: bold; color: #64748b; border-radius: 6px;")

        if not self.current_result:
            self.update_empty_dashboard()

    def update_empty_dashboard(self):
        title_color = "#94a3b8" if self.is_dark_mode else "#64748b"
        val_color = "#38bdf8" if self.is_dark_mode else "#0284c7"
        bg_color = "#0f172a" if self.is_dark_mode else "#f1f5f9"
        border_color = "#334155" if self.is_dark_mode else "#cbd5e1"

        card_style = f"background: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 8px;"
        
        self.lbl_sa_score.setText(f"<div style='text-align: center;'><span style='font-size: 12px; color: {title_color}; font-weight: normal;'>Synthetic Accessibility (SA) Score</span><br/><span style='font-size: 18px; color: {val_color}; font-weight: bold;'>--</span></div>")
        self.lbl_sa_score.setStyleSheet(card_style)

        self.lbl_tg.setText(f"<div style='text-align: center;'><span style='font-size: 12px; color: {title_color}; font-weight: normal;'>Glass Transition Temp (Tg)</span><br/><span style='font-size: 18px; color: {val_color}; font-weight: bold;'>--</span></div>")
        self.lbl_tg.setStyleSheet(card_style)

        val_density_color = "#f1f5f9" if self.is_dark_mode else "#0f172a"
        self.lbl_density.setText(f"<div style='text-align: center;'><span style='font-size: 12px; color: {title_color}; font-weight: normal;'>Density</span><br/><span style='font-size: 18px; color: {val_density_color}; font-weight: bold;'>--</span></div>")
        self.lbl_density.setStyleSheet(card_style)

    def update_result_ui(self, result: dict):
        sa = result.get("sa_score", "--")
        title_color = "#94a3b8" if self.is_dark_mode else "#64748b"
        bg_color = "#0f172a" if self.is_dark_mode else "#f1f5f9"
        border_color = "#334155" if self.is_dark_mode else "#cbd5e1"
        card_style = f"background: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 8px;"


        sa_green = "#4ade80" if self.is_dark_mode else "#16a34a"
        self.lbl_sa_score.setText(f"<div style='text-align: center;'><span style='font-size: 12px; color: {title_color}; font-weight: normal;'>Synthetic Accessibility (SA) Score</span><br/><span style='font-size: 18px; color: {sa_green}; font-weight: bold;'>{sa} (Synthesizable)</span></div>")
        self.lbl_sa_score.setStyleSheet(card_style)

        tg_blue = "#38bdf8" if self.is_dark_mode else "#0284c7"
        density_main = "#f1f5f9" if self.is_dark_mode else "#0f172a"

        preds = result.get("predictions", [])
        for p in preds:
            if "Glass Transition" in p["name"]:
                self.lbl_tg.setText(f"<div style='text-align: center;'><span style='font-size: 12px; color: {title_color}; font-weight: normal;'>Glass Transition Temp (Tg)</span><br/><span style='font-size: 18px; color: {tg_blue}; font-weight: bold;'>{p['value']} {p['unit']}</span></div>")
                self.lbl_tg.setStyleSheet(card_style)
            elif "Density" in p["name"]:
                self.lbl_density.setText(f"<div style='text-align: center;'><span style='font-size: 12px; color: {title_color}; font-weight: normal;'>Density</span><br/><span style='font-size: 18px; color: {density_main}; font-weight: bold;'>{p['value']} {p['unit']}</span></div>")
                self.lbl_density.setStyleSheet(card_style)

        if self.is_dark_mode:
            self.image_viewport.setStyleSheet("border: 2px solid #22c55e; background: #052e16; font-weight: bold; color: #4ade80; border-radius: 6px;")
        else:
            self.image_viewport.setStyleSheet("border: 2px solid #16a34a; background: #f0fdf4; font-weight: bold; color: #15803d; border-radius: 6px;")
        self.image_viewport.setText(f"Structure Rendered\nCanonical SMILES:\n{result.get('canonical_smiles')}")

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
        self.btn_save_db.setEnabled(True)
        self.current_result = result

        self.update_result_ui(result)
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
            
            # Check existing predictions for this molecule to prevent duplicate prediction stacking
            existing_history = self.db.fetch_history(limit=500)
            existing_record = next((item for item in existing_history if item["molecule_id"] == mol_id), None)
            
            if existing_record and existing_record["predictions"]:
                QMessageBox.information(self, "Database Persistence", f"Molecule record (ID: {mol_id}) and its predictions already exist in SQLite database!")
            else:
                for p in self.current_result.get("predictions", []):
                    self.db.insert_prediction(mol_id, p["name"], p["value"], p["unit"])
                QMessageBox.information(self, "Database Persistence", f"Successfully saved molecule record (ID: {mol_id}) to SQLite!")

            # Disable save button until a new pipeline prediction runs to prevent duplicate clicks
            self.btn_save_db.setEnabled(False)
            self.refresh_history_table()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save record: {str(e)}")


    def refresh_history_table(self):
        records = self.db.fetch_history()
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PolymerAppHomepage()
    window.show()
    sys.exit(app.exec())
