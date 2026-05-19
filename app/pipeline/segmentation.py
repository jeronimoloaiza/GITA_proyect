"""
Module: segmentation
Provides ROI selection and multi-Otsu segmentation.

"""
import numpy as np
from skimage.filters import threshold_multiotsu
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)


class _ROIImageLabel(QLabel):
    def __init__(self, pixmap):
        super().__init__()
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())
        self._start = None
        self._end = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start = event.pos()
            self._end = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if self._start is not None:
            self._end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._start is not None:
            self._end = event.pos()
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._start is None or self._end is None:
            return
        rect = QRect(self._start, self._end).normalized()
        painter = QPainter(self)
        painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
        painter.drawRect(rect)
        painter.end()

    def selected_rect(self):
        if self._start is None or self._end is None:
            return None
        rect = QRect(self._start, self._end).normalized()
        if rect.width() <= 1 or rect.height() <= 1:
            return None
        x1 = max(0, rect.left())
        y1 = max(0, rect.top())
        x2 = min(self.width(), rect.right() + 1)
        y2 = min(self.height(), rect.bottom() + 1)
        if x2 <= x1 or y2 <= y1:
            return None
        return x1, y1, x2, y2


class _ROISelectionDialog(QDialog):
    def __init__(self, image_gray, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select ROI")
        self._coords = None

        img_uint8 = (np.clip(image_gray, 0, 1) * 255).astype(np.uint8)
        h, w = img_uint8.shape
        qimg = QImage(img_uint8.data, w, h, w, QImage.Format_Grayscale8).copy()
        pixmap = QPixmap.fromImage(qimg)

        self.image_label = _ROIImageLabel(pixmap)
        scroll = QScrollArea()
        scroll.setWidget(self.image_label)
        scroll.setWidgetResizable(False)

        instructions = QLabel("Click y arrastra para seleccionar ROI. Luego presiona Confirmar.")

        confirm_btn = QPushButton("Confirmar")
        cancel_btn = QPushButton("Cancelar")
        confirm_btn.clicked.connect(self._confirm)
        cancel_btn.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(cancel_btn)

        layout = QVBoxLayout()
        layout.addWidget(instructions)
        layout.addWidget(scroll)
        layout.addLayout(button_layout)
        self.setLayout(layout)
        self.resize(min(w + 100, 1200), min(h + 140, 900))

    def _confirm(self):
        rect = self.image_label.selected_rect()
        if rect is None:
            QMessageBox.warning(self, "ROI inválido", "Selecciona una región válida antes de confirmar.")
            return
        self._coords = rect
        self.accept()

    def coords(self):
        return self._coords

def select_roi(image_gray):
    """
    Opens an interactive window to manually select a rectangular region of interest (ROI)
    from a grayscale image. Returns both the cropped ROI and its coordinates.

    Parameters
    ----------
    image_gray : np.ndarray
        Grayscale image with float32 values in [0, 1] range.

    Returns
    -------
    tuple
        - np.ndarray: Cropped region of interest (ROI)
        - tuple: Coordinates as (x1, y1, x2, y2)
    """
    dialog = _ROISelectionDialog(image_gray)
    if dialog.exec() != QDialog.Accepted:
        raise ValueError("No ROI was selected. Selection was cancelled.")

    coords = dialog.coords()
    if coords is None:
        raise ValueError("No ROI was selected. Please select a valid region.")

    x1, y1, x2, y2 = coords
    roi = image_gray[y1:y2, x1:x2]
    if roi.size == 0:
        raise ValueError("Selected ROI has zero area. Please select a valid region.")
    return roi, coords

def segment_multi_otsu(img_gray, n_classes=3):
    """
    Segment image using multi-Otsu thresholding.

    Parameters
    ----------
    img_gray : np.ndarray
        Input grayscale image (float32, range [0,1]).
    n_classes : int
        Number of classes (default=3: background + 2 levels of flakes).

    Returns
    -------
    np.ndarray
        Labeled image with values {0,1,...,n_classes-1}.
    np.ndarray
        Threshold values found by multi-Otsu.
    """
    thresholds = threshold_multiotsu(img_gray, classes=n_classes)
    segmented = np.digitize(img_gray, bins=thresholds)
    return segmented, thresholds
