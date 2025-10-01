"""
Pipeline package initializer.
Exposes core functions for image segmentation and analysis.

"""
from .visualization import show_loaded_image_and_green_channel, show_selected_roi, show_segmentation_and_histogram
from .upload import get_uploaded_image
from .preprocessing import preprocess_green_channel
from .segmentation import select_roi, segment_multi_otsu
from .analysis import visualize_overlay_by_class_and_contrast