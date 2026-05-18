"""
Module: preprocessing
Applies bilateral filtering to enhance contrast while preserving edges.
"""

import cv2
import numpy as np


def preprocess_green_channel(image_gray):
    """
    Applies bilateral filtering to the input grayscale image to reduce noise while preserving edges.
    This preprocessing step enhances the contrast and smoothness of the green channel before segmentation.

    Parameters
    ----------
    image_gray : np.ndarray
        Grayscale image (typically the green channel) with float32 values in [0, 1] range.

    Returns
    -------
    np.ndarray
        Denoised grayscale image with float32 values in [0, 1] range.
    """
    denoised = cv2.bilateralFilter((image_gray * 255).astype("uint8"), d=9, sigmaColor=75, sigmaSpace=75)
    denoised = denoised.astype("float32") / 255.0
    return denoised
