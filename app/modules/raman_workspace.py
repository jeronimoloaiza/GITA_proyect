"""
Module: raman_workspace
Base UI for Raman analysis workflows.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton


class RamanWorkspace(QWidget):
    def __init__(self, on_back):
        super().__init__()
        self._on_back = on_back
        self.setObjectName("workspace")

        layout = QVBoxLayout()

        header = QHBoxLayout()

        title = QLabel("Análisis Raman")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        description = QLabel(
            "Base de arquitectura creada.\n"
            "Aquí se integrarán carga de espectros, preprocesamiento y métricas Raman (D, G, 2D)."
        )
        description.setAlignment(Qt.AlignCenter)

        status = QLabel("Estado actual: módulo base listo para expandir.")
        status.setAlignment(Qt.AlignCenter)

        back_btn = QPushButton("← Volver al inicio")
        back_btn.setObjectName("backBtn")
        back_btn.setMinimumHeight(40)
        back_btn.clicked.connect(self._on_back)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(back_btn)

        layout.addLayout(header)
        layout.addWidget(description)
        layout.addWidget(status)
        layout.addStretch()

        self.setLayout(layout)
