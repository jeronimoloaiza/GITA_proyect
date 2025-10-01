"""
Module: upload
Handles image loading, normalization, and green channel extraction.

"""

import io
import numpy as np
from PIL import Image
import ipywidgets as widgets
import matplotlib.pyplot as plt

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


# testing

if __name__ == "__main__":
    from PIL import Image
    import numpy as np
    import matplotlib.pyplot as plt

    image_path = r"C:\Users\User\Documents\UdeA\GITA\graphene-segmentation\graphene-segmentation\assets\100x_04.jpg"
    image, green_image = get_uploaded_image(image_path)

    plt.imshow(image)
    plt.title("Loaded image from assets/")
    plt.axis("off")
    plt.show()

    plt.imshow(green_image, cmap="gray")
    plt.title("Green channel")
    plt.axis("off")
    plt.show()
