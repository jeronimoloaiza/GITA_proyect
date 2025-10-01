"""
Module: segmentation
Provides ROI selection and multi-Otsu segmentation.

"""
import cv2
import numpy as np
from skimage.filters import threshold_multiotsu
import matplotlib.pyplot as plt

def select_roi(image_gray):
    """
    Opens an interactive window to manually select a rectangular region of interest (ROI)
    from a grayscale image. Returns both the cropped ROI and its coordinates.

    Parameters
    ----------
    image_gray : np.ndarray
        Grayscale image with float32 values in [0, 1] range.

    Returns
    -------
    tuple
        - np.ndarray: Cropped region of interest (ROI)
        - tuple: Coordinates as (x1, y1, x2, y2)
    """
    img_uint8 = (image_gray * 255).astype("uint8")
    cv2.namedWindow("Select ROI", cv2.WINDOW_NORMAL)
    r = cv2.selectROI("Select ROI", img_uint8, showCrosshair=True)
    cv2.destroyAllWindows()
    x, y, w, h = r
    roi = image_gray[y:y+h, x:x+w]
    coords = (x, y, x+w, y+h)
    return roi, coords

def segment_multi_otsu(img_gray, n_classes=3):
    """
    Segment image using multi-Otsu thresholding.

    Parameters
    ----------
    img_gray : np.ndarray
        Input grayscale image (float32, range [0,1]).
    n_classes : int
        Number of classes (default=3: background + 2 levels of flakes).

    Returns
    -------
    np.ndarray
        Labeled image with values {0,1,...,n_classes-1}.
    np.ndarray
        Threshold values found by multi-Otsu.
    """
    thresholds = threshold_multiotsu(img_gray, classes=n_classes)
    segmented = np.digitize(img_gray, bins=thresholds)
    return segmented, thresholds

# testing

if __name__ == "__main__":
    from PIL import Image
    import numpy as np
    import matplotlib.pyplot as plt

    image_path = r"C:\Users\User\Documents\UdeA\GITA\graphene-segmentation\graphene-segmentation\assets\100x_04.jpg"
    image = Image.open(image_path).convert("RGB")
    image_np = np.array(image).astype(np.float32) / 255.0

    green_channel = image_np[:, :, 1]

    roi_img = select_roi(green_channel)
    segmented, thresholds = segment_multi_otsu(roi_img, n_classes=4)

    print("Thresholds:", thresholds)

    plt.figure(figsize=(12, 6))
    plt.subplot(1, 3, 1)
    plt.imshow(roi_img, cmap='gray')
    plt.title("Selected ROI")
    plt.axis("off")

    plt.subplot(1, 3, 2)
    plt.imshow(segmented, cmap='nipy_spectral')
    plt.title("Segmented Image")
    plt.axis("off")

    plt.subplot(1, 3, 3)
    plt.hist(roi_img.ravel(), bins=256)
    for t in thresholds:
        plt.axvline(t, color='r', linestyle='--')
    plt.title("Histogram with Thresholds")
    plt.xlabel("Pixel Intensity")
    plt.ylabel("Frequency")

    plt.tight_layout()
    plt.show()