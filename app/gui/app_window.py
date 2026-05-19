"""Main Qt window and app runner for the GUI package."""

import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QFont

from app.modules.segmentation_workspace import SegmentationWorkspace
from app.modules.optical_simulation_workspace import OpticalSimulationWorkspace
from app.modules.raman_workspace import RamanWorkspace


class HomeSelector(QWidget):
    def __init__(self, on_segmentation, on_optical_sim, on_raman):
        super().__init__()
        layout = QVBoxLayout()
        title = QLabel("Plataforma de análisis de grafeno")
        title.setObjectName("homeTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        subtitle = QLabel("Selecciona el flujo de trabajo")
        subtitle.setObjectName("homeSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        segmentation_btn = QPushButton("Segmentación (contraste óptico)")
        segmentation_btn.setObjectName("segmentationBtn")
        segmentation_btn.clicked.connect(on_segmentation)

        optical_btn = QPushButton("Simulación de contraste óptico")
        optical_btn.setObjectName("opticalBtn")
        optical_btn.clicked.connect(on_optical_sim)

        raman_btn = QPushButton("Análisis Raman")
        raman_btn.setObjectName("ramanBtn")
        raman_btn.clicked.connect(on_raman)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(segmentation_btn)
        layout.addWidget(optical_btn)
        layout.addWidget(raman_btn)
        layout.addStretch()

        self.setLayout(layout)


class GrapheneApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graphene Analysis Platform")
        self.setGeometry(100, 100, 1180, 800)
        self.setMinimumSize(1060, 720)

        layout = QVBoxLayout()
        self.stack = QStackedWidget()

        self.home_view = HomeSelector(
            on_segmentation=self.show_segmentation,
            on_optical_sim=self.show_optical_simulation,
            on_raman=self.show_raman,
        )
        self.segmentation_view = SegmentationWorkspace(on_back=self.show_home)
        self.optical_simulation_view = OpticalSimulationWorkspace(on_back=self.show_home)
        self.raman_view = RamanWorkspace(on_back=self.show_home)

        self.stack.addWidget(self.home_view)
        self.stack.addWidget(self.segmentation_view)
        self.stack.addWidget(self.optical_simulation_view)
        self.stack.addWidget(self.raman_view)

        layout.addWidget(self.stack)
        self.setLayout(layout)

    def show_home(self):
        self.stack.setCurrentWidget(self.home_view)

    def show_segmentation(self):
        self.stack.setCurrentWidget(self.segmentation_view)

    def show_optical_simulation(self):
        self.stack.setCurrentWidget(self.optical_simulation_view)

    def show_raman(self):
        self.stack.setCurrentWidget(self.raman_view)


def run_app():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set a modern default font (fallbacks in case font not available)
    app.setFont(QFont("Segoe UI", 10))

    # Load the QSS stylesheet if available
    try:
        with open("app/gui/style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except Exception:
        # if stylesheet not found, continue with palette and defaults
        pass

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, Qt.white)
    palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.black)
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.BrightText, Qt.white)
    palette.setColor(QPalette.Link, QColor(0, 0, 255))
    palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)

    window = GrapheneApp()
    window.show()
    return app.exec()
