"""
Module: visualization
Handles graphical display of image loading, ROI selection, and segmentation previews.
"""

import matplotlib.pyplot as plt
import numpy as np

def show_loaded_image_and_green_channel(image_rgb):
    """
    Displays the uploaded RGB image and its green channel side by side.

    Parameters
    ----------
    image_rgb : np.ndarray
        RGB image normalized to [0, 1].
    """
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    axes[0].imshow(image_rgb)
    axes[0].set_title("Uploaded RGB image")
    axes[1].imshow(image_rgb[:, :, 1], cmap="gray")
    axes[1].set_title("Green channel")
    for ax in axes:
        ax.axis("off")
    plt.tight_layout()
    plt.show()

def show_selected_roi(image_rgb, roi_coords):
    """
    Displays the selected ROI on top of the original image.

    Parameters
    ----------
    image_rgb : np.ndarray
        Original RGB image.
    roi_coords : tuple
        Coordinates of ROI as (x1, y1, x2, y2).
    """
    x1, y1, x2, y2 = roi_coords
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(image_rgb)
    rect = plt.Rectangle((x1, y1), x2 - x1, y2 - y1, edgecolor='red', facecolor='none', linewidth=2)
    ax.add_patch(rect)
    ax.set_title("Selected ROI")
    ax.axis("off")
    plt.tight_layout()
    plt.show()


def show_segmentation_and_histogram(image_gray, segmented, thresholds):
    """
    Displays original ROI, segmented image, and histogram with thresholds.

    Parameters
    ----------
    image_gray : np.ndarray
        Grayscale ROI image.
    segmented : np.ndarray
        Labeled image from Multi-Otsu.
    thresholds : list or np.ndarray
        Thresholds used for segmentation.
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].imshow(image_gray, cmap="gray")
    axes[0].set_title("ROI (grayscale)")
    axes[0].axis("off")

    axes[1].imshow(segmented, cmap="jet")
    axes[1].set_title("Segmented ROI (Multi-Otsu)")
    axes[1].axis("off")

    axes[2].hist(image_gray.ravel(), bins=256, histtype='step', color='black')
    for thresh in thresholds:
        axes[2].axvline(thresh, color='red', linestyle='--')
    axes[2].set_title("Histogram with thresholds")

    plt.tight_layout()
    plt.show()
