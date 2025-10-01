"""
Module: gui
Desktop GUI for graphene segmentation using PyQt5.

"""

import sys
import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QSpinBox
)
from PyQt5.QtCore import Qt
import numpy as np
from app.pipeline.upload import get_uploaded_image
from app.pipeline.preprocessing import preprocess_green_channel
from app.pipeline.segmentation import select_roi, segment_multi_otsu
from app.pipeline.analysis import visualize_overlay_by_class_and_contrast
from app.pipeline.visualization import (
    show_loaded_image_and_green_channel,
    show_selected_roi,
    show_segmentation_and_histogram
)

class GrapheneApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Graphene Segmentation")
        self.setGeometry(100, 100, 400, 400)

        self.image_rgb = None
        self.image_green = None
        self.roi = None
        self.roi_coords = None
        self.segmented = None
        self.thresholds = None
        self.background_class = None

        layout = QVBoxLayout()

        self.label = QLabel("Bienvenido al sistema de segmentación de grafeno")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.upload_btn = QPushButton("Cargar imagen")
        self.upload_btn.clicked.connect(self.load_image)
        layout.addWidget(self.upload_btn)

        self.roi_btn = QPushButton("Seleccionar ROI")
        self.roi_btn.clicked.connect(self.select_roi)
        self.roi_btn.setEnabled(False)
        layout.addWidget(self.roi_btn)

        self.class_count_label = QLabel("¿Cuántas zonas deseas segmentar?")
        self.class_count_input = QSpinBox()
        self.class_count_input.setMinimum(2)
        self.class_count_input.setMaximum(10)
        self.class_count_input.setValue(4)
        self.class_count_label.setEnabled(False)
        self.class_count_input.setEnabled(False)
        layout.addWidget(self.class_count_label)
        layout.addWidget(self.class_count_input)

        self.segment_btn = QPushButton("Segmentar ROI")
        self.segment_btn.clicked.connect(self.segment_roi)
        self.segment_btn.setEnabled(False)
        layout.addWidget(self.segment_btn)

        self.classify_btn = QPushButton("Clasificar")
        self.classify_btn.clicked.connect(self.classify_roi)
        self.classify_btn.setEnabled(False)
        layout.addWidget(self.classify_btn)

        self.setLayout(layout)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecciona una imagen", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.image_rgb, raw_green = get_uploaded_image(file_path)
            self.image_green = preprocess_green_channel(raw_green)
            show_loaded_image_and_green_channel(self.image_rgb)
            self.label.setText("Imagen cargada y preprocesada correctamente.")
            self.roi_btn.setEnabled(True)

    def select_roi(self):
        if self.image_green is None:
            self.label.setText("Primero debes cargar una imagen.")
            return
        self.label.setText("Selecciona una región con suficiente fondo para mejorar la clasificación.")
        self.roi, self.roi_coords = select_roi(self.image_green)
        show_selected_roi(self.image_rgb, self.roi_coords)
        self.label.setText("ROI seleccionado.")
        self.class_count_label.setEnabled(True)
        self.class_count_input.setEnabled(True)
        self.segment_btn.setEnabled(True)

    def segment_roi(self):
        if self.roi is None:
            self.label.setText("Primero debes seleccionar un ROI.")
            return
        n_classes = self.class_count_input.value()
        self.segmented, self.thresholds = segment_multi_otsu(self.roi, n_classes=n_classes)

        unique, counts = np.unique(self.segmented, return_counts=True)
        self.background_class = unique[np.argmax(counts)]

        show_segmentation_and_histogram(self.roi, self.segmented, self.thresholds)

        self.label.setText(
            f"Segmentación completada con {n_classes} zonas.\n"
            f"Clase más abundante detectada como fondo: {self.background_class}.\n"
            "Recuerda que el fondo no se clasifica."
        )
        self.classify_btn.setEnabled(True)

    def classify_roi(self):
        if self.roi is None or self.roi_coords is None or self.segmented is None or self.background_class is None:
            self.label.setText("Faltan datos para clasificar.")
            return

        visualize_overlay_by_class_and_contrast(
            segmented=self.segmented,
            img_gray=self.roi,
            full_image=self.image_rgb,
            background_class=self.background_class
        )

        self.label.setText("Clasificación completada.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GrapheneApp()
    window.show()
    sys.exit(app.exec_())