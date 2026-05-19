"""Reusable card that displays a titled image preview."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .image_tools import fit_pixmap, figure_to_pixmap, gray_to_pixmap, rgb_to_pixmap


class ExpandedFigureDialog(QDialog):
    """Modal dialog for displaying an expanded matplotlib figure."""

    def __init__(self, figure: Any, title: str = "Gráfica ampliada", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumSize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        pixmap = figure_to_pixmap(figure, width=950, height=650)
        image_label.setPixmap(pixmap)

        close_btn = QPushButton("Cerrar")
        close_btn.setMaximumWidth(120)
        close_btn.clicked.connect(self.close)

        layout.addWidget(image_label, 1)
        layout.addWidget(close_btn)
        self.setStyleSheet("QDialog { background: white; }")


class ImageCard(QFrame):
    expand_requested = Signal(object)  # Emits the stored figure when expand is clicked

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("displayCard")
        self.setMinimumWidth(240)
        self._current_figure: Any = None
        self._card_title = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title_bar = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.expand_btn = QPushButton("⤢")
        self.expand_btn.setObjectName("expandBtn")
        self.expand_btn.setMaximumWidth(36)
        self.expand_btn.setMaximumHeight(24)
        self.expand_btn.setToolTip("Expandir gráfica")
        self.expand_btn.clicked.connect(self._on_expand)
        self.expand_btn.setEnabled(False)

        title_bar.addWidget(self.title_label, 1)
        title_bar.addWidget(self.expand_btn)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(220)
        self.image_label.setMinimumWidth(220)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setStyleSheet(
            "background: #f7f9fc; border: 1px solid #e4e9f0; border-radius: 10px;"
        )

        layout.addLayout(title_bar)
        layout.addWidget(self.image_label, 1)

    def set_pixmap(self, pixmap, max_width=None, max_height=None, figure=None):
        """Set the pixmap and optionally store the figure for expand functionality.
        
        Parameters
        ----------
        pixmap : QPixmap
            Pixmap to display.
        max_width : int, optional
            Maximum width for scaling.
        max_height : int, optional
            Maximum height for scaling.
        figure : object, optional
            Matplotlib Figure object to store for expand dialog.
        """
        if pixmap is None:
            self.image_label.clear()
            self._current_figure = None
            return
        if max_width is not None and max_height is not None:
            pixmap = fit_pixmap(pixmap, max_width, max_height)
        self._current_figure = figure
        self.image_label.setPixmap(pixmap)
        self.expand_btn.setEnabled(figure is not None)

    def set_rgb_image(self, image_rgb, max_width=None, max_height=None):
        self.set_pixmap(rgb_to_pixmap(image_rgb), max_width, max_height)

    def set_gray_image(self, image_gray, max_width=None, max_height=None):
        self.set_pixmap(gray_to_pixmap(image_gray), max_width, max_height)

    def clear(self):
        self.image_label.clear()
        self._current_figure = None
        self.expand_btn.setEnabled(False)

    def _on_expand(self) -> None:
        """Emit expand_requested signal with the stored figure."""
        if self._current_figure is not None:
            self.expand_requested.emit(self._current_figure)
