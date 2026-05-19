"""
Module: visualization
Handles graphical display of image loading, ROI selection, segmentation previews,
and classification overlays.

ROI rendering stays in PySide6 (Qt). Other plots are displayed with Matplotlib.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout


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
    dialog.exec()


def show_loaded_image_and_green_channel(image_rgb):
    fig, axs = plt.subplots(1, 2, figsize=(14, 6))
    axs[0].imshow(np.clip(image_rgb, 0, 1) if image_rgb.dtype != np.uint8 else image_rgb)
    axs[0].set_title("Uploaded RGB image", fontsize=13)
    axs[0].axis("off")

    axs[1].imshow(image_rgb[:, :, 1], cmap="gray")
    axs[1].set_title("Green channel", fontsize=13)
    axs[1].axis("off")

    fig.suptitle("Imagen cargada", fontsize=15)
    plt.tight_layout()
    plt.show()


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
    fig, axs = plt.subplots(1, 3, figsize=(20, 6))

    axs[0].imshow(image_gray, cmap="gray")
    axs[0].set_title("ROI (grayscale)", fontsize=13)
    axs[0].axis("off")

    axs[1].imshow(segmented, cmap="tab20")
    axs[1].set_title("Segmented ROI (Multi-Otsu)", fontsize=13)
    axs[1].axis("off")

    axs[2].hist(np.clip(image_gray, 0, 1).ravel(), bins=256, range=(0, 1), color="steelblue", alpha=0.85)
    for thresh in thresholds:
        axs[2].axvline(float(np.clip(thresh, 0, 1)), color="red", linestyle="--", linewidth=2)
    axs[2].set_title("Histogram with thresholds", fontsize=13)
    axs[2].set_xlabel("Intensity")
    axs[2].set_ylabel("Pixel count")

    fig.suptitle("Segmentación ROI", fontsize=15)
    plt.tight_layout()
    plt.show()


def show_classification_overlay(img_gray, overlay_rgb, full_image, legend_entries, results_df=None):
    alpha = 0.4
    gray_rgb = np.stack([img_gray, img_gray, img_gray], axis=-1)
    overlay_view = np.clip((1 - alpha) * gray_rgb + alpha * overlay_rgb, 0, 1)

    fig = plt.figure(figsize=(20, 10))
    gs = fig.add_gridspec(2, 3, height_ratios=[3.2, 1.4])

    ax0 = fig.add_subplot(gs[0, 0])
    ax0.imshow(img_gray, cmap="gray")
    ax0.imshow(overlay_rgb, alpha=0.4)
    ax0.set_title("Overlay by class and physical interpretation", fontsize=13)
    ax0.axis("off")

    if legend_entries:
        handles = [mpatches.Patch(color=color, label=label) for label, color in legend_entries]
        ax0.legend(handles=handles, loc="lower right", fontsize=10, framealpha=0.9)

    ax1 = fig.add_subplot(gs[0, 1])
    ax1.imshow(img_gray, cmap="gray")
    ax1.set_title("Original ROI for segmentation", fontsize=13)
    ax1.axis("off")

    ax2 = fig.add_subplot(gs[0, 2])
    ax2.imshow(np.clip(full_image, 0, 1) if full_image.dtype != np.uint8 else full_image)
    ax2.set_title("Original full microscopy image", fontsize=13)
    ax2.axis("off")

    ax_table = fig.add_subplot(gs[1, :])
    ax_table.axis("off")
    if results_df is not None and not results_df.empty:
        display_df = results_df.sort_values(by="Contrast (%)", ascending=False).reset_index(drop=True)
        table = ax_table.table(
            cellText=display_df.values,
            colLabels=display_df.columns,
            loc="center",
            cellLoc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 1.6)
        ax_table.set_title("Summary by class", fontsize=13, pad=10)
    else:
        ax_table.text(0.5, 0.5, "No valid classes found for contrast analysis.", ha="center", va="center", fontsize=12)

    fig.suptitle("Clasificación por contraste", fontsize=16)
    plt.tight_layout()
    plt.show()
