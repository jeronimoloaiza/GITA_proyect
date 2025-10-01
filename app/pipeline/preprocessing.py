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
    # Apply bilateral filter to reduce noise while preserving edges
    denoised = cv2.bilateralFilter((image_gray * 255).astype("uint8"), d=9, sigmaColor=75, sigmaSpace=75)
    denoised = denoised.astype("float32") / 255.0
    return denoised
 
# testing

if __name__ == "__main__":
    from PIL import Image
    import numpy as np
    import matplotlib.pyplot as plt

    image_path = r"C:\Users\User\Documents\UdeA\GITA\graphene-segmentation\graphene-segmentation\assets\100x_04.jpg"
    image = Image.open(image_path).convert("RGB")
    image_np = np.array(image).astype(np.float32) / 255.0

    green_channel = image_np[:, :, 1]
    denoised_green = preprocess_green_channel(green_channel)

    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.imshow(green_channel, cmap='gray')
    plt.title("Original Green Channel")
    plt.axis("off")

    plt.subplot(1, 2, 2)
    plt.imshow(denoised_green, cmap='gray')
    plt.title("Denoised Green Channel")
    plt.axis("off")

    plt.show()