from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np


@dataclass
class SegmentationState:
    image_rgb: Optional[np.ndarray] = None
    image_green: Optional[np.ndarray] = None
    roi: Optional[np.ndarray] = None
    roi_coords: Optional[Tuple[int, int, int, int]] = None
    segmented: Optional[np.ndarray] = None
    thresholds: Optional[np.ndarray] = None
    background_class: Optional[int] = None
