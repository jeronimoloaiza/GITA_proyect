"""
Module: optical_simulation_workspace
Base UI for optical contrast simulation workflows.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class OpticalSimulationWorkspace(QWidget):
    def __init__(self, on_back):
        super().__init__()
        self._on_back = on_back

        layout = QVBoxLayout()

        title = QLabel("Simulación de contraste óptico")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 600;")

        description = QLabel(
            "Base de arquitectura creada.\n"
            "Aquí se integrarán simulaciones físicas/ópticas del contraste sobre Si/SiO₂."
        )
        description.setAlignment(Qt.AlignCenter)

        status = QLabel("Estado actual: módulo base listo para expandir.")
        status.setAlignment(Qt.AlignCenter)

        back_btn = QPushButton("← Volver al inicio")
        back_btn.clicked.connect(self._on_back)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(status)
        layout.addStretch()
        layout.addWidget(back_btn)

        self.setLayout(layout)
