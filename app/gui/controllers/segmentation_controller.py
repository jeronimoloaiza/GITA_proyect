"""SegmentationController: coordinates pipeline calls and keeps a SegmentationState."""
from PySide6.QtCore import QObject, Signal
import numpy as np

from app.gui.state.segmentation_state import SegmentationState
from app.pipeline.upload import get_uploaded_image
from app.pipeline.preprocessing import preprocess_green_channel
from app.pipeline.segmentation import select_roi, segment_multi_otsu
from app.pipeline.analysis import visualize_overlay_by_class_and_contrast
from PySide6.QtWidgets import QFileDialog


class SegmentationController(QObject):
    """Controller that encapsulates segmentation workflow logic.

    Signals
    -------
    state_changed: emits the current SegmentationState
    error: emits error messages (str)
    """

    state_changed = Signal(object)
    error = Signal(str)
    classification_requested = Signal(object)

    def __init__(self):
        super().__init__()
        self.state = SegmentationState()

    def load_image(self, parent=None):
        path, _ = QFileDialog.getOpenFileName(parent, "Selecciona una imagen", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        try:
            img, green = get_uploaded_image(path)
            self.state.image_rgb = img
            self.state.image_green = preprocess_green_channel(green)
            self.state_changed.emit(self.state)
        except Exception as e:
            self.error.emit(str(e))

    def select_roi(self):
        if self.state.image_green is None:
            self.error.emit("Primero debes cargar una imagen.")
            return
        try:
            roi, coords = select_roi(self.state.image_green)
            self.state.roi = roi
            self.state.roi_coords = coords
            self.state_changed.emit(self.state)
        except Exception as e:
            self.error.emit(str(e))

    def segment_roi(self, n_classes: int = 3):
        if self.state.roi is None:
            self.error.emit("Primero debes seleccionar un ROI.")
            return
        try:
            segmented, thresholds = segment_multi_otsu(self.state.roi, n_classes=n_classes)
            self.state.segmented = segmented
            self.state.thresholds = thresholds
            unique, counts = np.unique(segmented, return_counts=True)
            self.state.background_class = unique[np.argmax(counts)]
            self.state_changed.emit(self.state)
        except Exception as e:
            self.error.emit(str(e))

    def classify_roi(self):
        if self.state.roi is None or self.state.segmented is None or self.state.background_class is None:
            self.error.emit("Faltan datos para clasificar.")
            return
        # Request the UI to perform the classification visualization using current state
        try:
            self.classification_requested.emit(self.state)
        except Exception as e:
            self.error.emit(str(e))
