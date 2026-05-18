"""
Module: upload
Handles image loading, normalization, and green channel extraction.

"""

import numpy as np
from PIL import Image

def get_uploaded_image(file_path):
    """
    Loads an image from a file path and converts it to a normalized RGB array.

    Parameters
    ----------
    file_path : str
        Path to the image file.

    Returns
    -------
    tuple
        - np.ndarray: RGB image as float32 in [0, 1]
        - np.ndarray: Green channel as float32 in [0, 1]
    """
    img = Image.open(file_path).convert("RGB")
    img = np.array(img).astype(np.float32) / 255.0
    green_channel = img[:, :, 1]
    return img, green_channel

