"""Shared image conversion helpers used by multiple workspace panels."""

from __future__ import annotations

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap


def to_uint8_rgb(image_rgb):
    if image_rgb.dtype != np.uint8:
        image_rgb = (np.clip(image_rgb, 0, 1) * 255).astype(np.uint8)
    return image_rgb


def to_uint8_gray(image_gray):
    if image_gray.dtype != np.uint8:
        image_gray = (np.clip(image_gray, 0, 1) * 255).astype(np.uint8)
    return image_gray


def rgb_to_pixmap(image_rgb):
    image_rgb = to_uint8_rgb(image_rgb)
    height, width, _ = image_rgb.shape
    qimg = QImage(image_rgb.data, width, height, 3 * width, QImage.Format_RGB888).copy()
    return QPixmap.fromImage(qimg)


def gray_to_pixmap(image_gray):
    image_gray = to_uint8_gray(image_gray)
    height, width = image_gray.shape
    qimg = QImage(image_gray.data, width, height, width, QImage.Format_Grayscale8).copy()
    return QPixmap.fromImage(qimg)


def fit_pixmap(pixmap, max_width, max_height):
    return pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def figure_to_pixmap(figure, width=420, height=280):
    """Render a Matplotlib figure into a QPixmap.

    Parameters
    ----------
    figure : matplotlib.figure.Figure
        Figure to render.
    width : int, optional
        Output width in pixels. Default is 420.
    height : int, optional
        Output height in pixels. Default is 280.

    Returns
    -------
    QPixmap
        Rendered figure image.
    """

    canvas = FigureCanvas(figure)
    # Set target size in inches (assume 100 px/in by default)
    figure.set_size_inches(width / 100.0, height / 100.0, forward=True)
    # Ensure tight layout so labels/titles are not clipped after resize
    try:
        figure.tight_layout()
    except Exception:
        # If tight_layout fails for any reason, continue and let drawing proceed
        pass
    canvas.draw()
    # Use canvas reported pixel dimensions to construct the QImage correctly
    canvas_width, canvas_height = canvas.get_width_height()
    buffer = np.asarray(canvas.buffer_rgba())
    qimg = QImage(buffer.data, canvas_width, canvas_height, 4 * canvas_width, QImage.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimg)


def histogram_pixmap(image_gray, thresholds, width=420, height=280):
    image_gray = np.clip(image_gray, 0, 1)
    fig = Figure(figsize=(width / 100.0, height / 100.0), dpi=100)
    canvas = FigureCanvas(fig)
    ax = fig.add_subplot(111)
    ax.hist(image_gray.ravel(), bins=256, range=(0, 1), color="#3b82f6", alpha=0.88)
    threshold_values = [] if thresholds is None else np.atleast_1d(thresholds).tolist()
    for threshold in threshold_values:
        ax.axvline(float(np.clip(threshold, 0, 1)), color="#ef4444", linestyle="--", linewidth=2)
    ax.set_title("Histogram with thresholds", fontsize=11)
    ax.set_xlabel("Intensity", fontsize=10)
    ax.set_ylabel("Pixel count", fontsize=10)
    fig.tight_layout()
    canvas.draw()
    width, height = canvas.get_width_height()
    buffer = np.asarray(canvas.buffer_rgba())
    qimg = QImage(buffer.data, width, height, 4 * width, QImage.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimg)
