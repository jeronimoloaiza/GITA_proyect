"""Two-column optical contrast simulation workspace."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QWidget

from app.gui.widgets import OpticalSimulationControlPanel, OpticalSimulationDisplayPanel
from app.pipeline.optical_simulation import generate_simulation_figures


class OpticalSimulationWorkspace(QWidget):
    """Workspace that mirrors the segmentation layout for optical simulations."""

    def __init__(self, on_back):
        super().__init__()
        self._on_back = on_back
        self.setObjectName("opticalSimulationWorkspace")

        self.control_panel = OpticalSimulationControlPanel()
        self.display_panel = OpticalSimulationDisplayPanel()

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(18)
        root_layout.addWidget(self.control_panel)
        root_layout.addWidget(self.display_panel, 1)

        self._connect_ui()
        self._set_idle_state()

    def _connect_ui(self) -> None:
        self.control_panel.simulation_requested.connect(self._open_simulation)
        self.control_panel.back_requested.connect(self._on_back)
        self.display_panel.generate_requested.connect(self._generate_simulation)

    def _set_idle_state(self) -> None:
        self.display_panel.set_idle(
            title="Simulación de contraste óptico",
            message=(
                "Haz clic en 'Simulación' para configurar índices, espesores y rangos. "
                "La columna derecha mostrará los parámetros y las figuras generadas."
            ),
        )
        self.control_panel.set_feedback("Pulsa 'Simulación' para abrir el formulario de contraste óptico.")

    def _open_simulation(self) -> None:
        self.display_panel.show_simulation_page()
        self.control_panel.set_feedback("Completa los parámetros y pulsa 'Generar gráficas'.")

    def _generate_simulation(self) -> None:
        try:
            parameters = self.display_panel.collect_parameters()
            figures = generate_simulation_figures(
                incident_medium_index=parameters["incident_medium_index"],
                flake_index=parameters["flake_index"],
                oxide_index=parameters["oxide_index"],
                substrate_index=parameters["substrate_index"],
                single_layer_thickness_nm=parameters["single_layer_thickness_nm"],
                selected_layers=parameters["selected_layers"],
                layer_min=parameters["layer_min"],
                layer_max=parameters["layer_max"],
                wavelength_nm=parameters["wavelength_nm"],
                wavelength_min_nm=parameters["wavelength_min_nm"],
                wavelength_max_nm=parameters["wavelength_max_nm"],
                oxide_thickness_nm=parameters["oxide_thickness_nm"],
                oxide_min_nm=parameters["oxide_min_nm"],
                oxide_max_nm=parameters["oxide_max_nm"],
            )

            summary_text = (
                f"Índices: aire={parameters['incident_medium_index']}, flake={parameters['flake_index']}, "
                f"SiO2={parameters['oxide_index']}, Si={parameters['substrate_index']}. "
                f"Espesores: monocapa={parameters['single_layer_thickness_nm']:.3f} nm, "
                f"SiO2={parameters['oxide_thickness_nm']:.1f} nm. "
                f"Capas: N={parameters['selected_layers']} y rango [{parameters['layer_min']}, {parameters['layer_max']}]. "
                f"Longitud de onda: {parameters['wavelength_nm']:.1f} nm y rango [{parameters['wavelength_min_nm']:.1f}, {parameters['wavelength_max_nm']:.1f}] nm. "
                f"SiO2 rango [{parameters['oxide_min_nm']:.1f}, {parameters['oxide_max_nm']:.1f}] nm."
            )
            self.display_panel.show_results(figures, summary_text)
            self.control_panel.set_feedback("Simulación completada correctamente.")
        except Exception as exc:
            self.on_error(str(exc))

    def on_error(self, msg: str) -> None:
        self.control_panel.set_feedback(msg)
        QMessageBox.warning(self, "Error", msg)
