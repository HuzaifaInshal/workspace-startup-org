#!/usr/bin/env python3
"""Custom modern iOS/KDE Plasma 6 style animated Toggle Switch widget."""

from PyQt6.QtCore import Qt, pyqtProperty, pyqtSignal, QPropertyAnimation, QEasingCurve, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    """Sleek toggle switch with smooth animated knob transition."""

    toggled = pyqtSignal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._thumb_position = 1.0 if checked else 0.0
        self._track_radius = 11.0
        self._thumb_radius = 8.5

        self.setFixedSize(42, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"thumb_position", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    @pyqtProperty(float)
    def thumb_position(self) -> float:
        return self._thumb_position

    @thumb_position.setter
    def thumb_position(self, pos: float) -> None:
        self._thumb_position = pos
        self.update()

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if self._checked != checked:
            self._checked = checked
            self._anim.stop()
            self._anim.setStartValue(self._thumb_position)
            self._anim.setEndValue(1.0 if checked else 0.0)
            self._anim.start()
            self.toggled.emit(checked)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Track background color interpolation:
        # Off: rgba(255, 255, 255, 0.15) -> On: #3daee9
        off_color = QColor(255, 255, 255, 38)
        on_color = QColor(61, 174, 233, 235)
        
        r = int(off_color.red() + (on_color.red() - off_color.red()) * self._thumb_position)
        g = int(off_color.green() + (on_color.green() - off_color.green()) * self._thumb_position)
        b = int(off_color.blue() + (on_color.blue() - off_color.blue()) * self._thumb_position)
        a = int(off_color.alpha() + (on_color.alpha() - off_color.alpha()) * self._thumb_position)
        track_color = QColor(r, g, b, a)

        # Draw pill track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(QRectF(0, 0, w, h), self._track_radius, self._track_radius)

        # Draw knob thumb
        x_start = 2.5 + self._thumb_radius
        x_end = w - 2.5 - self._thumb_radius
        x_current = x_start + (x_end - x_start) * self._thumb_position
        y_current = h / 2.0

        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(
            QRectF(
                x_current - self._thumb_radius,
                y_current - self._thumb_radius,
                self._thumb_radius * 2,
                self._thumb_radius * 2,
            )
        )
