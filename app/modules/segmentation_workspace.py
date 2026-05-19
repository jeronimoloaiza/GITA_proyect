"""
Module: segmentation_workspace
UI workspace for graphene image segmentation and contrast-based classification.
"""

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpinBox, QMessageBox

from app.gui.controllers.segmentation_controller import SegmentationController
from app.pipeline.visualization import (
    show_loaded_image_and_green_channel,
    show_selected_roi,
    show_segmentation_and_histogram,
)
from app.pipeline.analysis import visualize_overlay_by_class_and_contrast


class SegmentationWorkspace(QWidget):
    """UI-only workspace for segmentation.

    The controller contains the business logic and updates a SegmentationState.
    The workspace subscribes to controller signals and updates presentation.
    """

    def __init__(self, on_back):
        super().__init__()
        self._on_back = on_back

        # controller handles pipeline and state
        self.controller = SegmentationController()
        self.controller.state_changed.connect(self.on_state_changed)
        self.controller.error.connect(self.on_error)
        self.controller.classification_requested.connect(self.on_classification_requested)

        self._build_ui()
        self._connect_ui()

        # initialize UI according to empty state
        self._update_ui()

    def _build_ui(self):
        layout = QVBoxLayout()

        self.label = QLabel("Segmentación de grafeno (contraste óptico)")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.upload_btn = QPushButton("Cargar imagen")
        layout.addWidget(self.upload_btn)

        self.roi_btn = QPushButton("Seleccionar ROI")
        self.roi_btn.setEnabled(False)
        layout.addWidget(self.roi_btn)

        self.class_count_label = QLabel("¿Cuántas zonas deseas segmentar?")
        self.class_count_input = QSpinBox()
        self.class_count_input.setMinimum(2)
        self.class_count_input.setMaximum(10)
        self.class_count_input.setValue(4)
        self.class_count_label.setEnabled(False)
        self.class_count_input.setEnabled(False)
        layout.addWidget(self.class_count_label)
        layout.addWidget(self.class_count_input)

        self.segment_btn = QPushButton("Segmentar ROI")
        self.segment_btn.setEnabled(False)
        layout.addWidget(self.segment_btn)

        self.classify_btn = QPushButton("Clasificar")
        self.classify_btn.setEnabled(False)
        layout.addWidget(self.classify_btn)

        self.back_btn = QPushButton("← Volver al inicio")
        layout.addWidget(self.back_btn)

        self.setLayout(layout)

    def _connect_ui(self):
        self.upload_btn.clicked.connect(lambda: self.controller.load_image(self))
        self.roi_btn.clicked.connect(self.controller.select_roi)
        self.segment_btn.clicked.connect(lambda: self.controller.segment_roi(self.class_count_input.value()))
        self.classify_btn.clicked.connect(self.controller.classify_roi)
        self.back_btn.clicked.connect(self._on_back)

    def on_state_changed(self, state):
        # update presentation from new state
        # show visualizations on first arrival of data
        # show loaded image when available
        if getattr(self, "_has_image", False) is False and state.image_rgb is not None:
            show_loaded_image_and_green_channel(state.image_rgb)
            self._has_image = True

        # show selected ROI when first available
        if getattr(self, "_has_roi", False) is False and state.roi_coords is not None:
            show_selected_roi(state.image_rgb, state.roi_coords)
            self._has_roi = True

        # show segmentation when first available
        if getattr(self, "_has_seg", False) is False and state.segmented is not None:
            show_segmentation_and_histogram(state.roi, state.segmented, state.thresholds)
            self._has_seg = True

        self._update_ui(state)

    def on_error(self, msg: str):
        # central place to report errors
        self.label.setText(msg)
        QMessageBox.warning(self, "Error", msg)

    def on_classification_requested(self, state):
        # The controller asks the UI to perform classification visualization
        try:
            visualize_overlay_by_class_and_contrast(
                segmented=state.segmented,
                img_gray=state.roi,
                full_image=state.image_rgb,
                background_class=state.background_class,
            )
        except Exception as e:
            self.on_error(str(e))

    def _update_ui(self, state=None):
        """Centralized UI updates based on the current state.

        If state is None we disable actions that require data.
        """
        if state is None:
            has_image = False
            has_roi = False
            has_seg = False
        else:
            has_image = state.image_green is not None
            has_roi = state.roi is not None
            has_seg = state.segmented is not None

        self.roi_btn.setEnabled(has_image)
        self.class_count_label.setEnabled(has_roi)
        self.class_count_input.setEnabled(has_roi)
        self.segment_btn.setEnabled(has_roi)
        self.classify_btn.setEnabled(has_seg)

