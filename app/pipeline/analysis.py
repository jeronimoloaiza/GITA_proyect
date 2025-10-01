"""
Module: analysis
Visualizes segmentation overlays and computes physical classification based on contrast.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from skimage import measure

def visualize_overlay_by_class_and_contrast(segmented, img_gray, full_image, background_class, min_size=50):
    """
    Displays a three-panel visualization of segmented regions and their physical interpretation based on contrast analysis.
    The function also returns a DataFrame summarizing region properties.

    Panels shown:
    1. Overlay by class with color-coded regions and physical interpretation (e.g., 1 layer, graphite)
    2. Original grayscale ROI used for segmentation
    3. Full microscopy image for context

    For each class (excluding background), the largest region is analyzed for contrast relative to the background.
    Based on contrast thresholds, the region is classified into physical categories such as graphene layers or graphite.

    Parameters
    ----------
    segmented : np.ndarray
        Labeled image with integer class values from segmentation.
    img_gray : np.ndarray
        Grayscale image used for contrast analysis (float32, range [0, 1]).
    full_image : np.ndarray
        Original full microscopy image for contextual display.
    background_class : int
        Label value corresponding to the background class.
    min_size : int, optional
        Minimum region area to be considered valid (default is 50 pixels).

    Returns
    -------
    pd.DataFrame
        Table containing class label, region area, contrast percentage, and physical classification.
    """

    background_intensity = np.median(img_gray[segmented == background_class])
    class_labels = [label for label in np.unique(segmented) if label != background_class]
    base_colors = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
    class_colors = {label: mcolors.to_rgb(base_colors[i % len(base_colors)]) for i, label in enumerate(class_labels)}

    overlay_rgb = np.zeros((*segmented.shape, 3), dtype=np.float32)
    legend_entries = []
    results = []

    for label in class_labels:
        mask = (segmented == label)
        labeled = measure.label(mask)
        regions = [r for r in measure.regionprops(labeled, intensity_image=img_gray) if r.area >= min_size]

        if not regions:
            continue

        region = max(regions, key=lambda r: r.area)
        contrast = (background_intensity - region.mean_intensity) / background_intensity * 100

        # Clasificación física extendida
        if 4 <= contrast <= 8:
            layer_type = "1 layer"
        elif 8 < contrast <= 11:
            layer_type = "2 layers"
        elif 11 < contrast <= 15:
            layer_type = "3 layers"
        elif 15 < contrast <= 18:
            layer_type = "4 layers"
        elif 18 < contrast <= 21:
            layer_type = "5 layers"
        elif contrast > 21:
            layer_type = "graphite"
        else:
            layer_type = "graphite"

        color = class_colors[label]
        for c in range(3):
            overlay_rgb[:, :, c] += ((segmented == label) * color[c]).astype(np.float32)

        legend_entries.append((f"Class {label}: {layer_type}", color))
        results.append({
            "Class": label,
            "Contrast (%)": round(contrast, 2),
            "Clasification": layer_type
        })

    # triple panel visualization
    fig, axs = plt.subplots(1, 3, figsize=(18,6))

    axs[0].imshow(img_gray, cmap="gray")
    axs[0].imshow(overlay_rgb, alpha=0.4)
    axs[0].set_title("overlay by class and physical interpretation")
    axs[0].axis("off")
    handles = [mpatches.Patch(color=color, label=label) for label, color in legend_entries]
    axs[0].legend(handles=handles, loc="lower right", framealpha=0.9)

    axs[1].imshow(img_gray, cmap="gray")
    axs[1].set_title("original ROI for segmentation")
    axs[1].axis("off")

    axs[2].imshow(full_image)
    axs[2].set_title("original full microscopy image")
    axs[2].axis("off")

    plt.tight_layout()
    plt.show()

    # Convert to DataFrame
    df_results = pd.DataFrame(results)
    return df_results

# testing

if __name__ == "__main__":
    from PIL import Image
    import numpy as np
    import matplotlib.pyplot as plt

    image_path = r"C:\Users\User\Documents\UdeA\GITA\graphene-segmentation\graphene-segmentation\assets\100x_04.jpg"
    image = Image.open(image_path).convert("RGB")
    image_np = np.array(image).astype(np.float32) / 255.0

    green_channel = image_np[:, :, 1]

    # Simulated segmented image for testing
    segmented = np.zeros_like(green_channel, dtype=np.int32)
    segmented[50:150, 50:150] = 1  # Class 1
    segmented[200:300, 200:300] = 2  # Class 2
    segmented[350:450, 350:450] = 3  # Class 3
    background_class = 0

    df_results = visualize_overlay_by_class_and_contrast(segmented, green_channel, image_np, background_class)
    print(df_results)