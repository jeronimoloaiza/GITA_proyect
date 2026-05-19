"""Interactive image canvas used for inline ROI selection."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from .image_tools import rgb_to_pixmap


class InteractiveImageCanvas(QWidget):
    """Inline canvas for displaying an image and drawing a rectangular ROI on it."""

    roi_selected = Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumHeight(420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._pixmap = None
        self._selection_mode = False
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self._roi_coords = None
        self._placeholder_text = "Carga una imagen para comenzar"

    def set_placeholder(self, text):
        self._pixmap = None
        self._selection_mode = False
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self._roi_coords = None
        self._placeholder_text = text
        self.update()

    def set_image(self, image_rgb):
        self._pixmap = rgb_to_pixmap(image_rgb)
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self.update()

    def set_selection_mode(self, enabled: bool):
        self._selection_mode = enabled and self._pixmap is not None
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self.update()

    def set_roi_coords(self, coords):
        self._roi_coords = coords
        self.update()

    def clear_roi_coords(self):
        self._roi_coords = None
        self.update()

    def _image_rect(self):
        if self._pixmap is None:
            return QRectF()
        margin = 18
        area = self.rect().adjusted(margin, margin, -margin, -margin)
        if area.width() <= 0 or area.height() <= 0:
            return QRectF()
        scale = min(area.width() / self._pixmap.width(), area.height() / self._pixmap.height())
        width = self._pixmap.width() * scale
        height = self._pixmap.height() * scale
        left = area.center().x() - (width / 2.0)
        top = area.center().y() - (height / 2.0)
        return QRectF(left, top, width, height)

    def _widget_to_image_point(self, pos, draw_rect):
        if not draw_rect.contains(pos):
            return None
        if self._pixmap is None or draw_rect.width() <= 0 or draw_rect.height() <= 0:
            return None
        scale_x = self._pixmap.width() / draw_rect.width()
        scale_y = self._pixmap.height() / draw_rect.height()
        x = int((pos.x() - draw_rect.left()) * scale_x)
        y = int((pos.y() - draw_rect.top()) * scale_y)
        x = max(0, min(self._pixmap.width() - 1, x))
        y = max(0, min(self._pixmap.height() - 1, y))
        return QPointF(x, y)

    def _image_to_widget_rect(self, coords, draw_rect):
        if self._pixmap is None:
            return QRectF()
        x1, y1, x2, y2 = coords
        scale_x = draw_rect.width() / self._pixmap.width()
        scale_y = draw_rect.height() / self._pixmap.height()
        left = draw_rect.left() + x1 * scale_x
        top = draw_rect.top() + y1 * scale_y
        width = (x2 - x1) * scale_x
        height = (y2 - y1) * scale_y
        return QRectF(left, top, width, height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor("#d9dde5"))

        if self._pixmap is None:
            painter.setPen(QColor("#6b7280"))
            title_font = QFont()
            title_font.setPointSize(12)
            title_font.setBold(True)
            painter.setFont(title_font)
            painter.drawText(self.rect(), Qt.AlignCenter, self._placeholder_text)
            painter.end()
            return

        draw_rect = self._image_rect()
        scaled = self._pixmap.scaled(draw_rect.size().toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(draw_rect.toRect(), scaled)

        if self._roi_coords is not None:
            roi_rect = self._image_to_widget_rect(self._roi_coords, draw_rect)
            painter.setPen(QPen(QColor("#e53935"), 3, Qt.SolidLine))
            painter.drawRect(roi_rect)

        if self._selection_mode and self._dragging and self._drag_start and self._drag_current:
            x1 = int(min(self._drag_start.x(), self._drag_current.x()))
            y1 = int(min(self._drag_start.y(), self._drag_current.y()))
            x2 = int(max(self._drag_start.x(), self._drag_current.x())) + 1
            y2 = int(max(self._drag_start.y(), self._drag_current.y())) + 1
            selection_rect = self._image_to_widget_rect((x1, y1, x2, y2), draw_rect)
            painter.setPen(QPen(QColor("#ff5252"), 3, Qt.DashLine))
            painter.drawRect(selection_rect)

        painter.end()

    def mousePressEvent(self, event):
        if not self._selection_mode or self._pixmap is None:
            return
        draw_rect = self._image_rect()
        point = self._widget_to_image_point(event.position(), draw_rect)
        if point is None:
            return
        self._dragging = True
        self._drag_start = point
        self._drag_current = point
        self.update()

    def mouseMoveEvent(self, event):
        if not self._selection_mode or not self._dragging or self._pixmap is None:
            return
        draw_rect = self._image_rect()
        point = self._widget_to_image_point(event.position(), draw_rect)
        if point is None:
            return
        self._drag_current = point
        self.update()

    def mouseReleaseEvent(self, event):
        if not self._selection_mode or not self._dragging or self._pixmap is None:
            return
        draw_rect = self._image_rect()
        point = self._widget_to_image_point(event.position(), draw_rect)
        if point is not None:
            self._drag_current = point
        if self._drag_start is None or self._drag_current is None:
            self._dragging = False
            self.update()
            return

        x1 = int(min(self._drag_start.x(), self._drag_current.x()))
        y1 = int(min(self._drag_start.y(), self._drag_current.y()))
        x2 = int(max(self._drag_start.x(), self._drag_current.x())) + 1
        y2 = int(max(self._drag_start.y(), self._drag_current.y())) + 1

        if x2 - x1 <= 1 or y2 - y1 <= 1:
            self._dragging = False
            self.update()
            return

        coords = (x1, y1, x2, y2)
        self._roi_coords = coords
        self._selection_mode = False
        self._dragging = False
        self._drag_start = None
        self._drag_current = None
        self.roi_selected.emit(coords)
        self.update()
