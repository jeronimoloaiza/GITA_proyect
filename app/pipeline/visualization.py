"""
Module: visualization
Handles graphical display of image loading, ROI selection, segmentation previews,
and classification overlays using PyQt5.
"""

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout


def _to_uint8_rgb(image_rgb):
    if image_rgb.dtype != np.uint8:
        image_rgb = (np.clip(image_rgb, 0, 1) * 255).astype(np.uint8)
    return image_rgb


def _to_uint8_gray(image_gray):
    if image_gray.dtype != np.uint8:
        image_gray = (np.clip(image_gray, 0, 1) * 255).astype(np.uint8)
    return image_gray


def _rgb_to_qpixmap(image_rgb):
    image_rgb = _to_uint8_rgb(image_rgb)
    h, w, _ = image_rgb.shape
    qimg = QImage(image_rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)


def _gray_to_qpixmap(image_gray):
    image_gray = _to_uint8_gray(image_gray)
    h, w = image_gray.shape
    qimg = QImage(image_gray.data, w, h, w, QImage.Format_Grayscale8).copy()
    return QPixmap.fromImage(qimg)


def _label_to_rgb(segmented):
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


def _build_histogram_pixmap(image_gray, thresholds, width=420, height=280):
    image_gray = np.clip(image_gray, 0, 1)
    hist, _ = np.histogram(image_gray.ravel(), bins=256, range=(0, 1))
    max_count = max(int(hist.max()), 1)

    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.white)
    painter = QPainter(pixmap)

    margin_left, margin_right, margin_top, margin_bottom = 40, 10, 20, 30
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    painter.setPen(QPen(Qt.black, 1))
    painter.drawRect(margin_left, margin_top, plot_w, plot_h)

    painter.setPen(QPen(Qt.black, 1))
    points = []
    for i, count in enumerate(hist):
        x = margin_left + int(i / 255.0 * plot_w)
        y = margin_top + plot_h - int((count / max_count) * plot_h)
        points.append((x, y))

    for i in range(len(points) - 1):
        painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

    painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
    for thresh in thresholds:
        t = float(np.clip(thresh, 0, 1))
        x = margin_left + int(t * plot_w)
        painter.drawLine(x, margin_top, x, margin_top + plot_h)

    painter.setPen(QPen(Qt.black, 1))
    painter.drawText(10, 15, "Histogram")
    painter.drawText(5, height - 5, "0")
    painter.drawText(width - 25, height - 5, "1")
    painter.end()
    return pixmap


def _show_images_dialog(title, panels, min_width=1000, min_height=460):
    dialog = QDialog()
    dialog.setWindowTitle(title)

    layout = QHBoxLayout()
    for panel_title, pixmap in panels:
        panel_layout = QVBoxLayout()
        title_label = QLabel(panel_title)
        title_label.setAlignment(Qt.AlignCenter)
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setPixmap(pixmap)
        panel_layout.addWidget(title_label)
        panel_layout.addWidget(image_label)
        layout.addLayout(panel_layout)

    dialog.setLayout(layout)
    dialog.resize(min_width, min_height)
    dialog.exec_()


def show_loaded_image_and_green_channel(image_rgb):
    rgb_pixmap = _rgb_to_qpixmap(image_rgb)
    green_pixmap = _gray_to_qpixmap(image_rgb[:, :, 1])
    _show_images_dialog(
        "Imagen cargada",
        [
            ("Uploaded RGB image", rgb_pixmap),
            ("Green channel", green_pixmap),
        ],
        min_width=900,
        min_height=420,
    )


def show_selected_roi(image_rgb, roi_coords):
    x1, y1, x2, y2 = roi_coords
    pixmap = _rgb_to_qpixmap(image_rgb)

    painter = QPainter(pixmap)
    painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
    painter.drawRect(x1, y1, max(1, x2 - x1), max(1, y2 - y1))
    painter.end()

    _show_images_dialog(
        "ROI seleccionado",
        [("Selected ROI", pixmap)],
        min_width=max(600, pixmap.width() + 80),
        min_height=max(480, pixmap.height() + 120),
    )


def show_segmentation_and_histogram(image_gray, segmented, thresholds):
    roi_pixmap = _gray_to_qpixmap(image_gray)
    seg_rgb = _label_to_rgb(segmented)
    segmented_pixmap = _rgb_to_qpixmap(seg_rgb)
    hist_pixmap = _build_histogram_pixmap(image_gray, thresholds)

    _show_images_dialog(
        "Segmentación ROI",
        [
            ("ROI (grayscale)", roi_pixmap),
            ("Segmented ROI (Multi-Otsu)", segmented_pixmap),
            ("Histogram with thresholds", hist_pixmap),
        ],
        min_width=1300,
        min_height=480,
    )


def show_classification_overlay(img_gray, overlay_rgb, full_image, legend_entries):
    alpha = 0.4
    gray_rgb = np.stack([img_gray, img_gray, img_gray], axis=-1)
    overlay_view = np.clip((1 - alpha) * gray_rgb + alpha * overlay_rgb, 0, 1)

    overlay_pixmap = _rgb_to_qpixmap(overlay_view)
    roi_pixmap = _gray_to_qpixmap(img_gray)
    full_pixmap = _rgb_to_qpixmap(full_image)

    dialog = QDialog()
    dialog.setWindowTitle("Clasificación por contraste")
    main_layout = QVBoxLayout()

    panels_layout = QHBoxLayout()
    for panel_title, pixmap in [
        ("Overlay by class and physical interpretation", overlay_pixmap),
        ("Original ROI for segmentation", roi_pixmap),
        ("Original full microscopy image", full_pixmap),
    ]:
        panel_layout = QVBoxLayout()
        title_label = QLabel(panel_title)
        title_label.setAlignment(Qt.AlignCenter)
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setPixmap(pixmap)
        panel_layout.addWidget(title_label)
        panel_layout.addWidget(image_label)
        panels_layout.addLayout(panel_layout)

    legend_text = "\n".join([f"{entry[0]}" for entry in legend_entries]) if legend_entries else "No classes found"
    legend_label = QLabel(legend_text)
    legend_label.setStyleSheet("padding: 6px;")

    main_layout.addLayout(panels_layout)
    main_layout.addWidget(QLabel("Legend:"))
    main_layout.addWidget(legend_label)
    dialog.setLayout(main_layout)
    dialog.resize(1400, 700)
    dialog.exec_()
