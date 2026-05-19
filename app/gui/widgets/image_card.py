"""Reusable card that displays a titled image preview."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout

from .image_tools import fit_pixmap, gray_to_pixmap, rgb_to_pixmap


class ImageCard(QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("displayCard")
        self.setMinimumWidth(240)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("cardTitle")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(220)
        self.image_label.setMinimumWidth(220)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet(
            "background: #f7f9fc; border: 1px solid #e4e9f0; border-radius: 10px;"
        )

        layout.addWidget(self.title_label)
        layout.addWidget(self.image_label, 1)

    def set_pixmap(self, pixmap, max_width=None, max_height=None):
        if pixmap is None:
            self.image_label.clear()
            return
        if max_width is not None and max_height is not None:
            pixmap = fit_pixmap(pixmap, max_width, max_height)
        self.image_label.setPixmap(pixmap)

    def set_rgb_image(self, image_rgb, max_width=None, max_height=None):
        self.set_pixmap(rgb_to_pixmap(image_rgb), max_width, max_height)

    def set_gray_image(self, image_gray, max_width=None, max_height=None):
        self.set_pixmap(gray_to_pixmap(image_gray), max_width, max_height)

    def clear(self):
        self.image_label.clear()
