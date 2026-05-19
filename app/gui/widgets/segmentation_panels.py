"""Reusable segmentation workspace panels."""

from __future__ import annotations

import numpy as np

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QPushButton,
)

from .image_card import ImageCard
from .image_tools import histogram_pixmap
from .interactive_image_canvas import InteractiveImageCanvas


class SegmentationControlPanel(QFrame):
    upload_requested = Signal()
    roi_requested = Signal()
    segment_requested = Signal()
    classify_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlPanel")
        self.setMaximumWidth(360)
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        self.title_label = QLabel("Segmentación")
        self.title_label.setObjectName("mainTitle")
        self.title_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("Flujo guiado de carga, selección de ROI, segmentación y clasificación.")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        self.feedback_label = QLabel("Cargue una imagen para comenzar.")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setObjectName("feedbackLabel")
        layout.addWidget(self.feedback_label)

        self.upload_btn = QPushButton("Cargar imagen")
        self.upload_btn.setObjectName("uploadBtn")
        self.upload_btn.setMinimumHeight(42)
        layout.addWidget(self.upload_btn)

        self.roi_btn = QPushButton("Seleccionar ROI")
        self.roi_btn.setObjectName("roiBtn")
        self.roi_btn.setMinimumHeight(42)
        self.roi_btn.setEnabled(False)
        layout.addWidget(self.roi_btn)

        self.class_count_label = QLabel("Partes a segmentar")
        self.class_count_label.setEnabled(False)
        layout.addWidget(self.class_count_label)

        self.class_count_input = QSpinBox()
        self.class_count_input.setMinimum(2)
        self.class_count_input.setMaximum(10)
        self.class_count_input.setValue(4)
        self.class_count_input.setEnabled(False)
        layout.addWidget(self.class_count_input)

        self.segment_btn = QPushButton("Segmentar ROI")
        self.segment_btn.setObjectName("segmentBtn")
        self.segment_btn.setMinimumHeight(42)
        self.segment_btn.setEnabled(False)
        layout.addWidget(self.segment_btn)

        self.classify_btn = QPushButton("Clasificar")
        self.classify_btn.setObjectName("classifyBtn")
        self.classify_btn.setMinimumHeight(42)
        self.classify_btn.setEnabled(False)
        layout.addWidget(self.classify_btn)

        layout.addStretch(1)

        self.back_btn = QPushButton("← Volver al inicio")
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setMinimumHeight(40)
        layout.addWidget(self.back_btn)

        self.upload_btn.clicked.connect(self.upload_requested.emit)
        self.roi_btn.clicked.connect(self.roi_requested.emit)
        self.segment_btn.clicked.connect(self.segment_requested.emit)
        self.classify_btn.clicked.connect(self.classify_requested.emit)
        self.back_btn.clicked.connect(self.back_requested.emit)

    def set_feedback(self, text):
        self.feedback_label.setText(text)

    def set_control_state(self, has_image=False, has_roi=False, has_segmentation=False):
        self.roi_btn.setEnabled(has_image)
        self.class_count_label.setEnabled(has_roi)
        self.class_count_input.setEnabled(has_roi)
        self.segment_btn.setEnabled(has_roi)
        self.classify_btn.setEnabled(has_segmentation)


class SegmentationDisplayPanel(QWidget):
    roi_selected = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        self.right_stack = QStackedWidget()
        layout.addWidget(self.right_stack, 1)

        self._build_canvas_page()
        self._build_segmentation_page()
        self._build_classification_page()

    def _build_canvas_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.canvas = InteractiveImageCanvas()
        self.canvas.roi_selected.connect(self.roi_selected.emit)

        self.canvas_hint = QLabel(
            "Carga una imagen y usa 'Seleccionar ROI' para dibujar directamente sobre la imagen de la derecha."
        )
        self.canvas_hint.setWordWrap(True)
        self.canvas_hint.setObjectName("displayHint")

        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.canvas_hint)
        self.right_stack.addWidget(page)
        self.canvas_page = page

    def _build_segmentation_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("Resultado de segmentación")
        title.setObjectName("mainTitle")
        layout.addWidget(title)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.seg_roi_card = ImageCard("ROI original")
        self.seg_mask_card = ImageCard("ROI segmentado")
        self.seg_hist_card = ImageCard("Histogram with thresholds")
        cards.addWidget(self.seg_roi_card, 1)
        cards.addWidget(self.seg_mask_card, 1)
        cards.addWidget(self.seg_hist_card, 1)
        layout.addLayout(cards)

        self.seg_summary_label = QLabel("Aquí aparecerán las clases y umbrales tras segmentar.")
        self.seg_summary_label.setWordWrap(True)
        self.seg_summary_label.setObjectName("displayHint")
        layout.addWidget(self.seg_summary_label)

        self.right_stack.addWidget(page)
        self.segmentation_page = page

    def _build_classification_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("Resultado de clasificación por contraste")
        title.setObjectName("mainTitle")
        layout.addWidget(title)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.cls_overlay_card = ImageCard("Overlay clasificado")
        self.cls_roi_card = ImageCard("ROI original")
        self.cls_full_card = ImageCard("Imagen completa")
        cards.addWidget(self.cls_overlay_card, 1)
        cards.addWidget(self.cls_roi_card, 1)
        cards.addWidget(self.cls_full_card, 1)
        layout.addLayout(cards)

        self.analysis_table = QTableWidget(0, 4)
        self.analysis_table.setObjectName("analysisTable")
        self.analysis_table.setHorizontalHeaderLabels(["Class", "Area (px)", "Contrast (%)", "Classification"])
        self.analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.analysis_table.setAlternatingRowColors(True)
        self.analysis_table.setMinimumHeight(180)
        layout.addWidget(self.analysis_table, 1)

        self.class_summary_label = QLabel("Aquí aparecerá la tabla de contraste y clasificación.")
        self.class_summary_label.setWordWrap(True)
        self.class_summary_label.setObjectName("displayHint")
        layout.addWidget(self.class_summary_label)

        self.right_stack.addWidget(page)
        self.classification_page = page

    def set_idle(self, canvas_placeholder, canvas_hint):
        self.right_stack.setCurrentWidget(self.canvas_page)
        self.canvas.set_placeholder(canvas_placeholder)
        self.canvas_hint.setText(canvas_hint)
        self.analysis_table.setRowCount(0)

    def show_loaded_image(self, image_rgb, roi_coords=None, canvas_hint=None):
        self.canvas.set_image(image_rgb)
        if roi_coords is not None:
            self.canvas.set_roi_coords(roi_coords)
        else:
            self.canvas.clear_roi_coords()
        self.right_stack.setCurrentWidget(self.canvas_page)
        if canvas_hint is not None:
            self.canvas_hint.setText(canvas_hint)

    def set_selection_mode(self, enabled, hint_text=None):
        self.canvas.set_selection_mode(enabled)
        if hint_text is not None:
            self.canvas_hint.setText(hint_text)

    def show_segmentation_results(self, roi, segmented, thresholds, background_class):
        self.right_stack.setCurrentWidget(self.segmentation_page)
        self.seg_roi_card.set_gray_image(roi, 420, 280)
        seg_rgb = self._label_to_rgb(segmented)
        self.seg_mask_card.set_rgb_image(seg_rgb, 420, 280)
        self.seg_hist_card.set_pixmap(histogram_pixmap(roi, thresholds), 420, 280)

        thresholds_txt = ", ".join([f"{threshold:.3f}" for threshold in thresholds]) if thresholds is not None else "-"
        self.seg_summary_label.setText(
            f"Umbrales: {thresholds_txt}. Clase de fondo: {background_class}. "
            "El siguiente paso es clasificar por contraste."
        )

    def show_classification_results(self, state, df_results, overlay_rgb):
        self.right_stack.setCurrentWidget(self.classification_page)
        self.cls_overlay_card.set_rgb_image(overlay_rgb, 360, 260)
        self.cls_roi_card.set_gray_image(state.roi, 360, 260)
        self.cls_full_card.set_rgb_image(state.image_rgb, 360, 260)

        self.analysis_table.setRowCount(0)
        if df_results is not None and not df_results.empty:
            display_df = df_results.sort_values(by="Contrast (%)", ascending=False).reset_index(drop=True)
            self.analysis_table.setRowCount(len(display_df))
            self.analysis_table.setColumnCount(len(display_df.columns))
            self.analysis_table.setHorizontalHeaderLabels([str(column) for column in display_df.columns])
            for row_idx, row in display_df.iterrows():
                for col_idx, column_name in enumerate(display_df.columns):
                    item = QTableWidgetItem(str(row[column_name]))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.analysis_table.setItem(row_idx, col_idx, item)
            self.analysis_table.resizeColumnsToContents()
            self.class_summary_label.setText(
                "Clasificación completada. La tabla muestra el contraste porcentual y la clasificación física por clase."
            )
        else:
            self.analysis_table.setRowCount(1)
            self.analysis_table.setColumnCount(1)
            self.analysis_table.setHorizontalHeaderLabels(["Info"])
            self.analysis_table.setItem(0, 0, QTableWidgetItem("No valid classes found for contrast analysis."))
            self.class_summary_label.setText("No se encontraron clases válidas para el análisis de contraste.")

    def _label_to_rgb(self, segmented):
        palette = np.array(
            [
                [0, 0, 0],
                [230, 25, 75],
                [60, 180, 75],
                [255, 225, 25],
                [0, 130, 200],
                [245, 130, 48],
                [145, 30, 180],
                [70, 240, 240],
                [240, 50, 230],
                [210, 245, 60],
                [250, 190, 190],
            ],
            dtype=np.uint8,
        )
        labels = segmented.astype(np.int32)
        labels = np.clip(labels, 0, len(palette) - 1)
        return palette[labels]
