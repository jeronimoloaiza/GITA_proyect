"""
Module: segmentation_workspace
Two-column segmentation workspace with an inline interactive ROI canvas.

The left panel contains the workflow controls.
The right panel shows the image, ROI selection, segmentation, and classification results
without opening extra windows.
"""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.gui.controllers.segmentation_controller import SegmentationController
from app.pipeline.analysis import analyze_contrast


def _to_uint8_rgb(image_rgb):
    if image_rgb.dtype != np.uint8:
        image_rgb = (np.clip(image_rgb, 0, 1) * 255).astype(np.uint8)
    return image_rgb


def _to_uint8_gray(image_gray):
    if image_gray.dtype != np.uint8:
        image_gray = (np.clip(image_gray, 0, 1) * 255).astype(np.uint8)
    return image_gray


def _rgb_to_pixmap(image_rgb):
    image_rgb = _to_uint8_rgb(image_rgb)
    h, w, _ = image_rgb.shape
    qimg = QImage(image_rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)


def _gray_to_pixmap(image_gray):
    image_gray = _to_uint8_gray(image_gray)
    h, w = image_gray.shape
    qimg = QImage(image_gray.data, w, h, w, QImage.Format_Grayscale8).copy()
    return QPixmap.fromImage(qimg)


def _fit_pixmap(pixmap, max_width, max_height):
    return pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def _histogram_pixmap(image_gray, thresholds, width=420, height=280):
    image_gray = np.clip(image_gray, 0, 1)
    fig = Figure(figsize=(width / 100.0, height / 100.0), dpi=100)
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.hist(image_gray.ravel(), bins=256, range=(0, 1), color="#3b82f6", alpha=0.88)
    threshold_values = [] if thresholds is None else np.atleast_1d(thresholds).tolist()
    for thresh in threshold_values:
        ax.axvline(float(np.clip(thresh, 0, 1)), color="#ef4444", linestyle="--", linewidth=2)
    ax.set_title("Histogram with thresholds", fontsize=11)
    ax.set_xlabel("Intensity", fontsize=10)
    ax.set_ylabel("Pixel count", fontsize=10)
    fig.tight_layout()
    canvas.draw()
    w, h = canvas.get_width_height()
    buffer = np.asarray(canvas.buffer_rgba())
    qimg = QImage(buffer.data, w, h, 4 * w, QImage.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimg)


class InteractiveImageCanvas(QWidget):
    """Inline canvas for displaying an image and drawing a rectangular ROI on it."""

    roi_selected = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumHeight(420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._pixmap = None
        self._selection_mode = False
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self._roi_coords = None
        self._placeholder_text = "Carga una imagen para comenzar"

    def set_placeholder(self, text):
        self._pixmap = None
        self._selection_mode = False
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self._roi_coords = None
        self._placeholder_text = text
        self.update()

    def set_image(self, image_rgb):
        self._pixmap = _rgb_to_pixmap(image_rgb)
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self.update()

    def set_selection_mode(self, enabled: bool):
        self._selection_mode = enabled and self._pixmap is not None
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self.update()

    def set_roi_coords(self, coords):
        self._roi_coords = coords
        self.update()

    def clear_roi_coords(self):
        self._roi_coords = None
        self.update()

    def _image_rect(self):
        if self._pixmap is None:
            return QRectF()
        margin = 18
        area = self.rect().adjusted(margin, margin, -margin, -margin)
        if area.width() <= 0 or area.height() <= 0:
            return QRectF()
        scale = min(area.width() / self._pixmap.width(), area.height() / self._pixmap.height())
        w = self._pixmap.width() * scale
        h = self._pixmap.height() * scale
        left = area.center().x() - (w / 2.0)
        top = area.center().y() - (h / 2.0)
        return QRectF(left, top, w, h)

    def _widget_to_image_point(self, pos, draw_rect):
        if not draw_rect.contains(pos):
            return None
        if self._pixmap is None or draw_rect.width() <= 0 or draw_rect.height() <= 0:
            return None
        scale_x = self._pixmap.width() / draw_rect.width()
        scale_y = self._pixmap.height() / draw_rect.height()
        x = int((pos.x() - draw_rect.left()) * scale_x)
        y = int((pos.y() - draw_rect.top()) * scale_y)
        x = max(0, min(self._pixmap.width() - 1, x))
        y = max(0, min(self._pixmap.height() - 1, y))
        return QPointF(x, y)

    def _image_to_widget_rect(self, coords, draw_rect):
        if self._pixmap is None:
            return QRectF()
        x1, y1, x2, y2 = coords
        scale_x = draw_rect.width() / self._pixmap.width()
        scale_y = draw_rect.height() / self._pixmap.height()
        left = draw_rect.left() + x1 * scale_x
        top = draw_rect.top() + y1 * scale_y
        w = (x2 - x1) * scale_x
        h = (y2 - y1) * scale_y
        return QRectF(left, top, w, h)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#d9dde5"))

        if self._pixmap is None:
            painter.setPen(QColor("#6b7280"))
            title_font = QFont()
            title_font.setPointSize(12)
            title_font.setBold(True)
            painter.setFont(title_font)
            painter.drawText(self.rect(), Qt.AlignCenter, self._placeholder_text)
            painter.end()
            return

        draw_rect = self._image_rect()
        scaled = self._pixmap.scaled(draw_rect.size().toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(draw_rect.toRect(), scaled)

        # Existing ROI overlay
        if self._roi_coords is not None:
            roi_rect = self._image_to_widget_rect(self._roi_coords, draw_rect)
            painter.setPen(QPen(QColor("#e53935"), 3, Qt.SolidLine))
            painter.drawRect(roi_rect)

        # Live selection overlay
        if self._selection_mode and self._dragging and self._drag_start and self._drag_current:
            x1 = int(min(self._drag_start.x(), self._drag_current.x()))
            y1 = int(min(self._drag_start.y(), self._drag_current.y()))
            x2 = int(max(self._drag_start.x(), self._drag_current.x())) + 1
            y2 = int(max(self._drag_start.y(), self._drag_current.y())) + 1
            sel_rect = self._image_to_widget_rect((x1, y1, x2, y2), draw_rect)
            painter.setPen(QPen(QColor("#ff5252"), 3, Qt.DashLine))
            painter.drawRect(sel_rect)

        painter.end()

    def mousePressEvent(self, event):
        if not self._selection_mode or self._pixmap is None:
            return
        draw_rect = self._image_rect()
        point = self._widget_to_image_point(event.position(), draw_rect)
        if point is None:
            return
        self._dragging = True
        self._drag_start = point
        self._drag_current = point
        self.update()

    def mouseMoveEvent(self, event):
        if not self._selection_mode or not self._dragging or self._pixmap is None:
            return
        draw_rect = self._image_rect()
        point = self._widget_to_image_point(event.position(), draw_rect)
        if point is None:
            return
        self._drag_current = point
        self.update()

    def mouseReleaseEvent(self, event):
        if not self._selection_mode or not self._dragging or self._pixmap is None:
            return
        draw_rect = self._image_rect()
        point = self._widget_to_image_point(event.position(), draw_rect)
        if point is not None:
            self._drag_current = point
        if self._drag_start is None or self._drag_current is None:
            self._dragging = False
            self.update()
            return

        x1 = int(min(self._drag_start.x(), self._drag_current.x()))
        y1 = int(min(self._drag_start.y(), self._drag_current.y()))
        x2 = int(max(self._drag_start.x(), self._drag_current.x())) + 1
        y2 = int(max(self._drag_start.y(), self._drag_current.y())) + 1

        if x2 - x1 <= 1 or y2 - y1 <= 1:
            self._dragging = False
            self.update()
            return

        coords = (x1, y1, x2, y2)
        self._roi_coords = coords
        self._selection_mode = False
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self.roi_selected.emit(coords)
        self.update()


class SegmentationWorkspace(QWidget):
    """Two-column segmentation workspace.

    Left: controls grouped in a narrow sidebar.
    Right: image canvas and embedded results pages.
    """

    def __init__(self, on_back):
        super().__init__()
        self._on_back = on_back
        self.setObjectName("segmentationWorkspace")

        self.controller = SegmentationController()
        self.controller.state_changed.connect(self.on_state_changed)
        self.controller.error.connect(self.on_error)

        self._build_ui()
        self._connect_ui()
        self._set_idle_state()

    def _build_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(18)

        # Left control panel
        self.control_frame = QFrame()
        self.control_frame.setObjectName("controlPanel")
        self.control_frame.setMaximumWidth(360)
        self.control_frame.setMinimumWidth(300)
        control_layout = QVBoxLayout(self.control_frame)
        control_layout.setContentsMargins(18, 18, 18, 18)
        control_layout.setSpacing(14)

        self.title_label = QLabel("Segmentación")
        self.title_label.setObjectName("mainTitle")
        self.title_label.setAlignment(Qt.AlignLeft)
        control_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("Flujo guiado de carga, selección de ROI, segmentación y clasificación.")
        self.subtitle_label.setWordWrap(True)
        control_layout.addWidget(self.subtitle_label)

        self.feedback_label = QLabel("Cargue una imagen para comenzar.")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setObjectName("feedbackLabel")
        control_layout.addWidget(self.feedback_label)

        self.upload_btn = QPushButton("Cargar imagen")
        self.upload_btn.setObjectName("uploadBtn")
        self.upload_btn.setMinimumHeight(42)
        control_layout.addWidget(self.upload_btn)

        self.roi_btn = QPushButton("Seleccionar ROI")
        self.roi_btn.setObjectName("roiBtn")
        self.roi_btn.setMinimumHeight(42)
        self.roi_btn.setEnabled(False)
        control_layout.addWidget(self.roi_btn)

        self.class_count_label = QLabel("Partes a segmentar")
        self.class_count_label.setEnabled(False)
        control_layout.addWidget(self.class_count_label)

        self.class_count_input = QSpinBox()
        self.class_count_input.setMinimum(2)
        self.class_count_input.setMaximum(10)
        self.class_count_input.setValue(4)
        self.class_count_input.setEnabled(False)
        control_layout.addWidget(self.class_count_input)

        self.segment_btn = QPushButton("Segmentar ROI")
        self.segment_btn.setObjectName("segmentBtn")
        self.segment_btn.setMinimumHeight(42)
        self.segment_btn.setEnabled(False)
        control_layout.addWidget(self.segment_btn)

        self.classify_btn = QPushButton("Clasificar")
        self.classify_btn.setObjectName("classifyBtn")
        self.classify_btn.setMinimumHeight(42)
        self.classify_btn.setEnabled(False)
        control_layout.addWidget(self.classify_btn)

        control_layout.addStretch(1)

        self.back_btn = QPushButton("← Volver al inicio")
        self.back_btn.setObjectName("backBtn")
        self.back_btn.setMinimumHeight(40)
        control_layout.addWidget(self.back_btn)

        # Right display panel
        self.display_frame = QFrame()
        self.display_frame.setObjectName("displayPanel")
        display_layout = QVBoxLayout(self.display_frame)
        display_layout.setContentsMargins(16, 16, 16, 16)
        display_layout.setSpacing(14)

        self.right_stack = QStackedWidget()
        display_layout.addWidget(self.right_stack, 1)

        self._build_canvas_page()
        self._build_segmentation_page()
        self._build_classification_page()

        root_layout.addWidget(self.control_frame)
        root_layout.addWidget(self.display_frame, 1)

    def _build_canvas_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.canvas = InteractiveImageCanvas()
        self.canvas.roi_selected.connect(self._on_roi_selected)

        self.canvas_hint = QLabel(
            "Carga una imagen y usa 'Seleccionar ROI' para dibujar directamente sobre la imagen de la derecha."
        )
        self.canvas_hint.setWordWrap(True)
        self.canvas_hint.setObjectName("displayHint")

        layout.addWidget(self.canvas, 1)
        layout.addWidget(self.canvas_hint)
        self.right_stack.addWidget(page)
        self.canvas_page = page

    def _make_image_card(self, title):
        frame = QFrame()
        frame.setObjectName("displayCard")
        frame.setMinimumWidth(240)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("cardTitle")
        image = QLabel()
        image.setAlignment(Qt.AlignCenter)
        image.setMinimumHeight(220)
        image.setMinimumWidth(220)
        image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        image.setStyleSheet("background: #f7f9fc; border: 1px solid #e4e9f0; border-radius: 10px;")

        layout.addWidget(label)
        layout.addWidget(image, 1)
        return frame, image

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
        self.seg_roi_card, self.seg_roi_label = self._make_image_card("ROI original")
        self.seg_mask_card, self.seg_mask_label = self._make_image_card("ROI segmentado")
        self.seg_hist_card, self.seg_hist_label = self._make_image_card("Histogram with thresholds")
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
        self.cls_overlay_card, self.cls_overlay_label = self._make_image_card("Overlay clasificado")
        self.cls_roi_card, self.cls_roi_label = self._make_image_card("ROI original")
        self.cls_full_card, self.cls_full_label = self._make_image_card("Imagen completa")
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

    def _connect_ui(self):
        self.upload_btn.clicked.connect(lambda: self.controller.load_image(self))
        self.roi_btn.clicked.connect(self._start_roi_selection)
        self.segment_btn.clicked.connect(self._segment_roi)
        self.classify_btn.clicked.connect(self._classify_roi)
        self.back_btn.clicked.connect(self._on_back)

    def _set_idle_state(self):
        self.right_stack.setCurrentWidget(self.canvas_page)
        self.canvas.set_placeholder("Carga una imagen para comenzar")
        self.canvas_hint.setText(
            "El panel derecho se usará para cargar la imagen, seleccionar el ROI y mostrar los resultados sin ventanas nuevas."
        )
        self.feedback_label.setText("Cargue una imagen para comenzar.")
        self.roi_btn.setEnabled(False)
        self.class_count_label.setEnabled(False)
        self.class_count_input.setEnabled(False)
        self.segment_btn.setEnabled(False)
        self.classify_btn.setEnabled(False)

    def on_state_changed(self, state):
        if state.image_rgb is not None:
            self.canvas.set_image(state.image_rgb)
            if state.roi_coords is not None:
                self.canvas.set_roi_coords(state.roi_coords)
            else:
                self.canvas.clear_roi_coords()
            self.right_stack.setCurrentWidget(self.canvas_page)
            self.canvas_hint.setText("Usa 'Seleccionar ROI' para dibujar directamente sobre la imagen.")
            self.feedback_label.setText("Imagen cargada. Puede seleccionar un ROI.")
        else:
            self._set_idle_state()
            return

        if state.roi is not None and state.roi_coords is not None:
            x1, y1, x2, y2 = state.roi_coords
            self.feedback_label.setText(f"ROI seleccionado: {x2 - x1} x {y2 - y1} px")
            self.canvas_hint.setText("ROI seleccionado. Ya puede segmentar la región elegida.")

        if state.segmented is not None and state.roi is not None:
            self._show_segmentation_results(state)

        self._update_controls(state)

    def _update_controls(self, state):
        has_image = state.image_green is not None
        has_roi = state.roi is not None
        has_seg = state.segmented is not None

        self.roi_btn.setEnabled(has_image)
        self.class_count_label.setEnabled(has_roi)
        self.class_count_input.setEnabled(has_roi)
        self.segment_btn.setEnabled(has_roi)
        self.classify_btn.setEnabled(has_seg)

    def _start_roi_selection(self):
        if self.controller.state.image_rgb is None:
            self.on_error("Primero debes cargar una imagen.")
            return
        self.right_stack.setCurrentWidget(self.canvas_page)
        self.canvas.set_selection_mode(True)
        self.feedback_label.setText("Arrastra sobre la imagen de la derecha para seleccionar el ROI.")
        self.canvas_hint.setText("Modo selección activo: presiona y arrastra para dibujar el ROI.")

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
        self.canvas.set_roi_coords(coords)
        self.canvas.set_selection_mode(False)
        self.canvas_hint.setText("ROI guardado. Ahora puede segmentar la región elegida.")

    def _segment_roi(self):
        if self.controller.state.roi is None:
            self.on_error("Primero debes seleccionar un ROI.")
            return
        self.controller.segment_roi(self.class_count_input.value())

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
        self._show_classification_results(state, df_results, overlay_rgb, legend_entries)

    def _show_segmentation_results(self, state):
        self.right_stack.setCurrentWidget(self.segmentation_page)
        self.seg_roi_label.setPixmap(_fit_pixmap(_gray_to_pixmap(state.roi), 420, 280))
        seg_rgb = self._label_to_rgb(state.segmented)
        self.seg_mask_label.setPixmap(_fit_pixmap(_rgb_to_pixmap(seg_rgb), 420, 280))
        self.seg_hist_label.setPixmap(_fit_pixmap(_histogram_pixmap(state.roi, state.thresholds), 420, 280))

        thresholds_txt = ", ".join([f"{t:.3f}" for t in state.thresholds]) if state.thresholds is not None else "-"
        self.seg_summary_label.setText(
            f"Umbrales: {thresholds_txt}. Clase de fondo: {state.background_class}. "
            "El siguiente paso es clasificar por contraste."
        )

    def _show_classification_results(self, state, df_results, overlay_rgb, legend_entries):
        self.right_stack.setCurrentWidget(self.classification_page)
        self.cls_overlay_label.setPixmap(_fit_pixmap(_rgb_to_pixmap(overlay_rgb), 360, 260))
        self.cls_roi_label.setPixmap(_fit_pixmap(_gray_to_pixmap(state.roi), 360, 260))
        self.cls_full_label.setPixmap(_fit_pixmap(_rgb_to_pixmap(state.image_rgb), 360, 260))

        self.analysis_table.setRowCount(0)
        if df_results is not None and not df_results.empty:
            display_df = df_results.sort_values(by="Contrast (%)", ascending=False).reset_index(drop=True)
            self.analysis_table.setRowCount(len(display_df))
            self.analysis_table.setColumnCount(len(display_df.columns))
            self.analysis_table.setHorizontalHeaderLabels([str(c) for c in display_df.columns])
            for row_idx, row in display_df.iterrows():
                for col_idx, col_name in enumerate(display_df.columns):
                    item = QTableWidgetItem(str(row[col_name]))
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

    def on_error(self, msg: str):
        self.feedback_label.setText(msg)
        QMessageBox.warning(self, "Error", msg)

