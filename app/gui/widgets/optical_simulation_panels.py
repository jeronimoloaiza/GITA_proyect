"""Reusable panels for the optical contrast simulation workspace."""

from __future__ import annotations

from typing import Any

import matplotlib.pyplot as plt
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.gui.widgets.image_card import ExpandedFigureDialog, ImageCard
from app.gui.widgets.image_tools import figure_to_pixmap
from app.pipeline.optical_simulation import (
    DEFAULT_CLIP_RANGE,
    DEFAULT_INCIDENT_MEDIUM_INDEX,
    DEFAULT_OXIDE_INDEX,
    DEFAULT_SUBSTRATE_INDEX,
    get_material_preset,
    parse_complex_index,
)


class OpticalSimulationControlPanel(QFrame):
    """Left control panel for the optical simulation workflow."""

    simulation_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("simulationControlPanel")
        self.setMaximumWidth(360)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("Simulación")
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)

        subtitle = QLabel(
            "Configura índices, espesores y rangos para generar las curvas y mapas de contraste óptico."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.feedback_label = QLabel("Pulsa 'Simulación' para comenzar.")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setObjectName("feedbackLabel")
        layout.addWidget(self.feedback_label)

        self.simulation_btn = QPushButton("Simulación")
        self.simulation_btn.setObjectName("uploadBtn")
        self.simulation_btn.setMinimumHeight(42)
        layout.addWidget(self.simulation_btn)

        layout.addStretch(1)

        self.back_btn = QPushButton("← Volver al inicio")
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setMinimumHeight(40)
        layout.addWidget(self.back_btn)

        self.simulation_btn.clicked.connect(self.simulation_requested.emit)
        self.back_btn.clicked.connect(self.back_requested.emit)

    def set_feedback(self, text: str) -> None:
        """Update the feedback label shown in the control panel."""

        self.feedback_label.setText(text)


class OpticalSimulationDisplayPanel(QWidget):
    """Right-side panel that holds parameters and simulation outputs."""

    generate_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("simulationDisplayPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        self.right_stack = QStackedWidget()
        layout.addWidget(self.right_stack, 1)

        self._build_idle_page()
        self._build_simulation_page()

    def _build_idle_page(self) -> None:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)

        title = QLabel("Simulación de contraste óptico")
        title.setObjectName("mainTitle")
        page_layout.addWidget(title)

        message = QLabel(
            "El panel derecho se usa para ingresar parámetros físicos y mostrar las gráficas del modelo Fresnel."
        )
        message.setWordWrap(True)
        message.setObjectName("displayHint")
        page_layout.addWidget(message)

        page_layout.addStretch(1)
        self.right_stack.addWidget(page)
        self.idle_page = page
        self.idle_message_label = message

    def _build_field_block(self, label_text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)

        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        container_layout.addWidget(label)
        container_layout.addWidget(widget)
        return container

    def _build_section(self, title_text: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("displayCard")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(14, 14, 14, 14)
        frame_layout.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("sectionTitle")
        frame_layout.addWidget(title)
        return frame, frame_layout

    def _build_simulation_page(self) -> None:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)

        title = QLabel("Simulación de contraste óptico")
        title.setObjectName("mainTitle")
        content_layout.addWidget(title)

        self.summary_label = QLabel("Completa los parámetros y genera todas las gráficas en un solo paso.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setObjectName("displayHint")
        content_layout.addWidget(self.summary_label)

        index_section, index_layout = self._build_section("Índices de refracción")
        index_row = QHBoxLayout()
        index_row.setSpacing(12)

        self.incident_index_edit = QLineEdit("1")
        self.incident_index_edit.setPlaceholderText("1 o (1+0j)")
        index_row.addWidget(self._build_field_block("Medio incidente", self.incident_index_edit), 1)

        flake_index_box = QWidget()
        flake_index_layout = QHBoxLayout(flake_index_box)
        flake_index_layout.setContentsMargins(0, 0, 0, 0)
        flake_index_layout.setSpacing(8)
        self.flake_index_edit = QLineEdit()
        self.flake_index_edit.setPlaceholderText("(1+2j)")
        self.flake_index_preset_combo = QComboBox()
        self.flake_index_preset_combo.addItems(["Manual", "Graphene", "MoS2"])
        self.flake_index_preset_combo.currentTextChanged.connect(self._apply_flake_index_preset)
        self.flake_index_preset_combo.setCurrentText("Graphene")
        flake_index_layout.addWidget(self.flake_index_edit, 1)
        flake_index_layout.addWidget(self.flake_index_preset_combo)
        index_row.addWidget(self._build_field_block("Índice del flake", flake_index_box), 1)

        self.oxide_index_edit = QLineEdit(str(DEFAULT_OXIDE_INDEX))
        self.oxide_index_edit.setPlaceholderText("1.46")
        index_row.addWidget(self._build_field_block("Índice del SiO2", self.oxide_index_edit), 1)

        self.substrate_index_edit = QLineEdit(str(DEFAULT_SUBSTRATE_INDEX))
        self.substrate_index_edit.setPlaceholderText("5.6-0.4j")
        index_row.addWidget(self._build_field_block("Índice del Si", self.substrate_index_edit), 1)

        index_layout.addLayout(index_row)
        content_layout.addWidget(index_section)

        thickness_section, thickness_layout = self._build_section("Grosores")
        thickness_row = QHBoxLayout()
        thickness_row.setSpacing(12)

        thickness_box = QWidget()
        thickness_box_layout = QHBoxLayout(thickness_box)
        thickness_box_layout.setContentsMargins(0, 0, 0, 0)
        thickness_box_layout.setSpacing(8)
        self.single_layer_thickness_spin = QDoubleSpinBox()
        self.single_layer_thickness_spin.setDecimals(3)
        self.single_layer_thickness_spin.setRange(0.001, 100.0)
        self.single_layer_thickness_spin.setSingleStep(0.001)
        self.single_layer_thickness_spin.setValue(0.335)
        self.single_layer_thickness_preset_combo = QComboBox()
        self.single_layer_thickness_preset_combo.addItems(["Manual", "Graphene", "MoS2"])
        self.single_layer_thickness_preset_combo.currentTextChanged.connect(self._apply_single_layer_thickness_preset)
        thickness_box_layout.addWidget(self.single_layer_thickness_spin, 1)
        thickness_box_layout.addWidget(self.single_layer_thickness_preset_combo)
        thickness_row.addWidget(self._build_field_block("Monocapa del flake (nm)", thickness_box), 1)

        self.oxide_thickness_spin = QDoubleSpinBox()
        self.oxide_thickness_spin.setDecimals(1)
        self.oxide_thickness_spin.setRange(0.0, 1000.0)
        self.oxide_thickness_spin.setSingleStep(1.0)
        self.oxide_thickness_spin.setValue(300.0)
        thickness_row.addWidget(self._build_field_block("SiO2 específico (nm)", self.oxide_thickness_spin), 1)

        oxide_range_box = QWidget()
        oxide_range_layout = QHBoxLayout(oxide_range_box)
        oxide_range_layout.setContentsMargins(0, 0, 0, 0)
        oxide_range_layout.setSpacing(8)
        self.oxide_min_spin = QDoubleSpinBox()
        self.oxide_min_spin.setDecimals(1)
        self.oxide_min_spin.setRange(0.0, 400.0)
        self.oxide_min_spin.setValue(0.0)
        self.oxide_max_spin = QDoubleSpinBox()
        self.oxide_max_spin.setDecimals(1)
        self.oxide_max_spin.setRange(0.0, 400.0)
        self.oxide_max_spin.setValue(400.0)
        oxide_range_layout.addWidget(self.oxide_min_spin, 1)
        oxide_range_layout.addWidget(self.oxide_max_spin, 1)
        thickness_row.addWidget(self._build_field_block("Rango SiO2 (nm)", oxide_range_box), 1)

        thickness_layout.addLayout(thickness_row)
        content_layout.addWidget(thickness_section)

        layers_section, layers_layout = self._build_section("Capas")
        layers_row = QHBoxLayout()
        layers_row.setSpacing(12)

        self.layer_count_spin = QSpinBox()
        self.layer_count_spin.setRange(0, 2147483647)
        self.layer_count_spin.setValue(1)
        layers_row.addWidget(self._build_field_block("Número de capas", self.layer_count_spin), 1)

        layer_range_box = QWidget()
        layer_range_layout = QHBoxLayout(layer_range_box)
        layer_range_layout.setContentsMargins(0, 0, 0, 0)
        layer_range_layout.setSpacing(8)
        self.layer_min_spin = QSpinBox()
        self.layer_min_spin.setRange(0, 2147483647)
        self.layer_min_spin.setValue(0)
        self.layer_max_spin = QSpinBox()
        self.layer_max_spin.setRange(0, 2147483647)
        self.layer_max_spin.setValue(10)
        layer_range_layout.addWidget(self.layer_min_spin, 1)
        layer_range_layout.addWidget(self.layer_max_spin, 1)
        layers_row.addWidget(self._build_field_block("Rango de capas", layer_range_box), 1)

        layers_layout.addLayout(layers_row)
        content_layout.addWidget(layers_section)

        wavelength_section, wavelength_layout = self._build_section("Longitudes de onda")
        wavelength_row = QHBoxLayout()
        wavelength_row.setSpacing(12)

        self.wavelength_spin = QDoubleSpinBox()
        self.wavelength_spin.setDecimals(1)
        self.wavelength_spin.setRange(1.0, 1000000000.0)
        self.wavelength_spin.setSingleStep(1.0)
        self.wavelength_spin.setValue(550.0)
        wavelength_row.addWidget(self._build_field_block("Longitud de onda específica (nm)", self.wavelength_spin), 1)

        wavelength_range_box = QWidget()
        wavelength_range_layout = QHBoxLayout(wavelength_range_box)
        wavelength_range_layout.setContentsMargins(0, 0, 0, 0)
        wavelength_range_layout.setSpacing(8)
        self.wavelength_min_spin = QDoubleSpinBox()
        self.wavelength_min_spin.setDecimals(1)
        self.wavelength_min_spin.setRange(1.0, 1000000000.0)
        self.wavelength_min_spin.setValue(400.0)
        self.wavelength_max_spin = QDoubleSpinBox()
        self.wavelength_max_spin.setDecimals(1)
        self.wavelength_max_spin.setRange(1.0, 1000000000.0)
        self.wavelength_max_spin.setValue(800.0)
        wavelength_range_layout.addWidget(self.wavelength_min_spin, 1)
        wavelength_range_layout.addWidget(self.wavelength_max_spin, 1)
        wavelength_row.addWidget(self._build_field_block("Rango de longitud de onda (nm)", wavelength_range_box), 1)

        wavelength_layout.addLayout(wavelength_row)
        content_layout.addWidget(wavelength_section)

        self.generate_btn = QPushButton("Generar gráficas")
        self.generate_btn.setObjectName("segmentBtn")
        self.generate_btn.setMinimumHeight(42)
        self.generate_btn.clicked.connect(self.generate_requested.emit)
        content_layout.addWidget(self.generate_btn)

        plots_section, plots_layout = self._build_section("Resultados")
        self.wavelength_plot_card = ImageCard("Contraste vs longitud de onda")
        self.layers_plot_card = ImageCard("Contraste vs número de capas")
        self.oxide_heatmap_card = ImageCard("Mapa λ vs SiO2")
        self.layers_heatmap_card = ImageCard("Mapa λ vs capas")

        plots_grid = QGridLayout()
        plots_grid.setSpacing(12)
        plots_grid.addWidget(self.wavelength_plot_card, 0, 0)
        plots_grid.addWidget(self.layers_plot_card, 0, 1)
        plots_grid.addWidget(self.oxide_heatmap_card, 1, 0)
        plots_grid.addWidget(self.layers_heatmap_card, 1, 1)
        plots_layout.addLayout(plots_grid)

        # Connect expand button signals to open enlarged dialogs
        self.wavelength_plot_card.expand_requested.connect(
            lambda fig: self._show_expanded_figure(fig, "Contraste vs longitud de onda")
        )
        self.layers_plot_card.expand_requested.connect(
            lambda fig: self._show_expanded_figure(fig, "Contraste vs número de capas")
        )
        self.oxide_heatmap_card.expand_requested.connect(
            lambda fig: self._show_expanded_figure(fig, "Mapa λ vs SiO2")
        )
        self.layers_heatmap_card.expand_requested.connect(
            lambda fig: self._show_expanded_figure(fig, "Mapa λ vs capas")
        )

        content_layout.addWidget(plots_section)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        page_layout.addWidget(scroll)
        self.right_stack.addWidget(page)
        self.simulation_page = page

    def _apply_flake_index_preset(self, material_name: str) -> None:
        """Fill the flake index field when a supported preset is selected."""

        if material_name == "Manual":
            return
        preset = get_material_preset(material_name)
        self.flake_index_edit.setText(str(preset["flake_index"]))

    def _apply_single_layer_thickness_preset(self, material_name: str) -> None:
        """Fill the single-layer thickness field when a supported preset is selected."""

        if material_name == "Manual":
            return
        preset = get_material_preset(material_name)
        self.single_layer_thickness_spin.setValue(float(preset["single_layer_thickness_nm"]))

    def set_idle(self, title: str, message: str) -> None:
        """Show the idle page and reset the summary text."""

        self.right_stack.setCurrentWidget(self.idle_page)
        self.idle_page.setWindowTitle(title)
        self.idle_message_label.setText(message)
        self.summary_label.setText("Completa los parámetros y genera todas las gráficas en un solo paso.")

    def show_simulation_page(self) -> None:
        """Switch to the simulation form and plot page."""

        self.right_stack.setCurrentWidget(self.simulation_page)

    def collect_parameters(self) -> dict[str, Any]:
        """Collect and validate the current simulation inputs.

        Returns
        -------
        dict[str, Any]
            Normalized simulation parameters ready for the plotting functions.
        """

        incident_medium_index = parse_complex_index(
            self.incident_index_edit.text(),
            default=DEFAULT_INCIDENT_MEDIUM_INDEX,
        )
        flake_index = parse_complex_index(self.flake_index_edit.text())
        oxide_index = parse_complex_index(self.oxide_index_edit.text(), default=DEFAULT_OXIDE_INDEX)
        substrate_index = parse_complex_index(self.substrate_index_edit.text(), default=DEFAULT_SUBSTRATE_INDEX)

        layer_min = min(self.layer_min_spin.value(), self.layer_max_spin.value())
        layer_max = max(self.layer_min_spin.value(), self.layer_max_spin.value())
        oxide_min_nm = min(self.oxide_min_spin.value(), self.oxide_max_spin.value())
        oxide_max_nm = max(self.oxide_min_spin.value(), self.oxide_max_spin.value())
        wavelength_min_nm = min(self.wavelength_min_spin.value(), self.wavelength_max_spin.value())
        wavelength_max_nm = max(self.wavelength_min_spin.value(), self.wavelength_max_spin.value())

        if layer_max < layer_min:
            raise ValueError("The layer range is invalid.")
        if oxide_max_nm < oxide_min_nm:
            raise ValueError("The SiO2 thickness range is invalid.")
        if wavelength_max_nm < wavelength_min_nm:
            raise ValueError("The wavelength range is invalid.")

        return {
            "incident_medium_index": incident_medium_index,
            "flake_index": flake_index,
            "oxide_index": oxide_index,
            "substrate_index": substrate_index,
            "single_layer_thickness_nm": self.single_layer_thickness_spin.value(),
            "selected_layers": self.layer_count_spin.value(),
            "layer_min": layer_min,
            "layer_max": layer_max,
            "wavelength_nm": self.wavelength_spin.value(),
            "wavelength_min_nm": wavelength_min_nm,
            "wavelength_max_nm": wavelength_max_nm,
            "oxide_thickness_nm": self.oxide_thickness_spin.value(),
            "oxide_min_nm": oxide_min_nm,
            "oxide_max_nm": oxide_max_nm,
            "clip_range": DEFAULT_CLIP_RANGE,
        }

    def show_results(self, figures: dict[str, Any], summary_text: str) -> None:
        """Render generated figures and update the summary label."""

        self.show_simulation_page()
        self.summary_label.setText(summary_text)

        card_map = (
            (self.wavelength_plot_card, figures.get("wavelength_contrast")),
            (self.layers_plot_card, figures.get("layer_contrast")),
            (self.oxide_heatmap_card, figures.get("wavelength_oxide_heatmap")),
            (self.layers_heatmap_card, figures.get("wavelength_layers_heatmap")),
        )
        for card, figure in card_map:
            if figure is None:
                card.clear()
                continue
            card.set_pixmap(figure_to_pixmap(figure), 420, 280, figure=figure)
            plt.close(figure)

    def _show_expanded_figure(self, figure: Any, title: str) -> None:
        """Open a modal dialog displaying an expanded figure.
        
        Parameters
        ----------
        figure : matplotlib.figure.Figure
            The figure to display in the expanded dialog.
        title : str
            Title for the dialog.
        """
        dialog = ExpandedFigureDialog(figure, title=title, parent=self)
        dialog.exec()

    def clear_results(self) -> None:
        """Clear all plotted outputs."""

        self.wavelength_plot_card.clear()
        self.layers_plot_card.clear()
        self.oxide_heatmap_card.clear()
        self.layers_heatmap_card.clear()

        self.summary_label.setText("Completa los parámetros y genera todas las gráficas en un solo paso.")
