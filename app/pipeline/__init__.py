"""
Pipeline package initializer.
Exposes core functions for image segmentation and analysis.

"""
from .visualization import show_loaded_image_and_green_channel, show_selected_roi, show_segmentation_and_histogram
from .upload import get_uploaded_image
from .preprocessing import preprocess_green_channel
from .segmentation import select_roi, segment_multi_otsu
from .analysis import visualize_overlay_by_class_and_contrast
from .optical_simulation import (
	DEFAULT_CLIP_RANGE,
	DEFAULT_INCIDENT_MEDIUM_INDEX,
	DEFAULT_OXIDE_INDEX,
	DEFAULT_SUBSTRATE_INDEX,
	MATERIAL_PRESETS,
	generate_simulation_figures,
	get_material_preset,
	optical_contrast,
	parse_complex_index,
)