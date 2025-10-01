"""
Module: upload
Handles image loading, normalization, and green channel extraction.

"""

import io
import numpy as np
from PIL import Image
import ipywidgets as widgets
import matplotlib.pyplot as plt

def get_uploaded_image(uploader):
    """
    Loads an uploaded image from a Jupyter FileUpload widget and converts it to a normalized RGB array.

    Parameters
    ----------
    uploader : widgets.FileUpload
        FileUpload widget containing the uploaded image.

    Returns
    -------
    np.ndarray or None
        RGB image as a NumPy array with float32 values in [0, 1] range.
        Returns None if no file is uploaded.
    """

    if uploader.value:
        # Get first uploaded file (UploadedFile object)
        file_info = uploader.value[0]
        img = Image.open(io.BytesIO(file_info.content)).convert("RGB")
        img = np.array(img).astype(np.float32) / 255.0
        green_channel = img[:, :, 1]
        return img, green_channel
    else:
        print("No file uploaded yet.")
        return None, None

# testing

if __name__ == "__main__":
    from PIL import Image
    import numpy as np
    import matplotlib.pyplot as plt

    image_path = r"C:\Users\User\Documents\UdeA\GITA\graphene-segmentation\graphene-segmentation\assets\100x_04.jpg"
    image = Image.open(image_path).convert("RGB")
    image_np = np.array(image).astype(np.float32) / 255.0

    plt.imshow(image_np)
    plt.title("Loaded image from assets/")
    plt.axis("off")
    plt.show()
