"""Segmentación de grafeno con paneles reutilizables."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QMessageBox, QWidget

from app.gui.controllers.segmentation_controller import SegmentationController
from app.gui.widgets import SegmentationControlPanel, SegmentationDisplayPanel
from app.pipeline.analysis import analyze_contrast


class SegmentationWorkspace(QWidget):
    """Two-column segmentation workspace built from reusable UI panels."""

    def __init__(self, on_back):
        super().__init__()
        self._on_back = on_back
        self.setObjectName("segmentationWorkspace")

        self.controller = SegmentationController()
        self.controller.state_changed.connect(self.on_state_changed)
        self.controller.error.connect(self.on_error)

        self.control_panel = SegmentationControlPanel()
        self.display_panel = SegmentationDisplayPanel()

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(18)
        root_layout.addWidget(self.control_panel)
        root_layout.addWidget(self.display_panel, 1)

        self._connect_ui()
        self._set_idle_state()

    def _connect_ui(self):
        self.control_panel.upload_requested.connect(lambda: self.controller.load_image(self))
        self.control_panel.roi_requested.connect(self._start_roi_selection)
        self.control_panel.segment_requested.connect(self._segment_roi)
        self.control_panel.classify_requested.connect(self._classify_roi)
        self.control_panel.back_requested.connect(self._on_back)
        self.display_panel.roi_selected.connect(self._on_roi_selected)

    def _set_idle_state(self):
        self.display_panel.set_idle(
            canvas_placeholder="Carga una imagen para comenzar",
            canvas_hint=(
                "El panel derecho se usará para cargar la imagen, seleccionar el ROI y mostrar los resultados sin ventanas nuevas."
            ),
        )
        self.control_panel.set_feedback("Cargue una imagen para comenzar.")
        self.control_panel.set_control_state()

    def on_state_changed(self, state):
        if state.image_rgb is None:
            self._set_idle_state()
            return

        self.display_panel.show_loaded_image(
            state.image_rgb,
            roi_coords=state.roi_coords,
            canvas_hint="Usa 'Seleccionar ROI' para dibujar directamente sobre la imagen.",
        )
        self.control_panel.set_feedback("Imagen cargada. Puede seleccionar un ROI.")

        if state.roi is not None and state.roi_coords is not None:
            x1, y1, x2, y2 = state.roi_coords
            self.control_panel.set_feedback(f"ROI seleccionado: {x2 - x1} x {y2 - y1} px")
            self.display_panel.canvas_hint.setText("ROI seleccionado. Ya puede segmentar la región elegida.")

        if state.segmented is not None and state.roi is not None:
            self.display_panel.show_segmentation_results(
                roi=state.roi,
                segmented=state.segmented,
                thresholds=state.thresholds,
                background_class=state.background_class,
            )

        self._update_controls(state)

    def _update_controls(self, state):
        has_image = state.image_green is not None
        has_roi = state.roi is not None
        has_segmentation = state.segmented is not None

        self.control_panel.set_control_state(
            has_image=has_image,
            has_roi=has_roi,
            has_segmentation=has_segmentation,
        )

    def _start_roi_selection(self):
        if self.controller.state.image_rgb is None:
            self.on_error("Primero debes cargar una imagen.")
            return
        self.display_panel.right_stack.setCurrentWidget(self.display_panel.canvas_page)
        self.display_panel.set_selection_mode(
            True,
            hint_text="Modo selección activo: presiona y arrastra para dibujar el ROI.",
        )
        self.control_panel.set_feedback("Arrastra sobre la imagen de la derecha para seleccionar el ROI.")

    def _on_roi_selected(self, coords):
        image_green = self.controller.state.image_green
        if image_green is None:
            self.on_error("Primero debes cargar una imagen.")
            return

        x1, y1, x2, y2 = coords
        roi = image_green[y1:y2, x1:x2]
        if roi.size == 0:
            self.on_error("El ROI seleccionado no tiene área válida.")
            return

        self.controller.set_roi(roi, coords)
        self.display_panel.canvas.set_roi_coords(coords)
        self.display_panel.set_selection_mode(False)
        self.display_panel.canvas_hint.setText("ROI guardado. Ahora puede segmentar la región elegida.")

    def _segment_roi(self):
        if self.controller.state.roi is None:
            self.on_error("Primero debes seleccionar un ROI.")
            return
        self.controller.segment_roi(self.control_panel.class_count_input.value())

    def _classify_roi(self):
        state = self.controller.state
        if state.roi is None or state.segmented is None or state.background_class is None:
            self.on_error("Faltan datos para clasificar.")
            return

        df_results, overlay_rgb, legend_entries = analyze_contrast(
            segmented=state.segmented,
            img_gray=state.roi,
            background_class=state.background_class,
        )
        self.display_panel.show_classification_results(state, df_results, overlay_rgb, legend_entries)

    def on_error(self, msg: str):
        self.control_panel.set_feedback(msg)
        QMessageBox.warning(self, "Error", msg)
