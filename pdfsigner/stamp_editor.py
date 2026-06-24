import os
import time
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QGridLayout,
    QLineEdit, QFileDialog, QMessageBox, QComboBox,
)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen

from pdfsigner.settings import StampProfile, BUILT_IN_PROFILES


class StampPreviewDialog(QDialog):
    stamp_position_changed = pyqtSignal(float, float)

    def __init__(self, profile: StampProfile, cert_name="", reason="", parent=None):
        super().__init__(parent)
        self.profile = profile
        self.cert_name = cert_name
        self.reason = reason
        self.dragging = False
        self.drag_offset = QPoint()
        self.stamp_x = 0.0
        self.stamp_y = 0.0
        self.setWindowTitle("Stamp Editor")
        self.setMinimumSize(900, 700)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        controls = QGridLayout()

        controls.addWidget(QLabel("Width (mm):"), 0, 0)
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(40, 200)
        self.width_spin.setValue(self.profile.width_mm)
        self.width_spin.valueChanged.connect(self._on_param_changed)
        controls.addWidget(self.width_spin, 0, 1)

        controls.addWidget(QLabel("Height (mm):"), 0, 2)
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(15, 100)
        self.height_spin.setValue(self.profile.height_mm)
        self.height_spin.valueChanged.connect(self._on_param_changed)
        controls.addWidget(self.height_spin, 0, 3)

        controls.addWidget(QLabel("Font size:"), 1, 0)
        self.font_spin = QDoubleSpinBox()
        self.font_spin.setRange(4, 16)
        self.font_spin.setValue(self.profile.font_size)
        self.font_spin.valueChanged.connect(self._on_param_changed)
        controls.addWidget(self.font_spin, 1, 1)

        controls.addWidget(QLabel("Position:"), 1, 2)
        self.position_combo = QComboBox()
        self.position_combo.addItems(["bottom-right", "bottom-left", "top-right", "top-left"])
        self.position_combo.setCurrentText(self.profile.position)
        self.position_combo.currentTextChanged.connect(self._on_param_changed)
        controls.addWidget(self.position_combo, 1, 3)

        self.include_owner = QCheckBox("Owner")
        self.include_owner.setChecked(self.profile.include_owner)
        self.include_owner.toggled.connect(self._on_param_changed)
        controls.addWidget(self.include_owner, 2, 0)

        self.include_issuer = QCheckBox("Issuer")
        self.include_issuer.setChecked(self.profile.include_issuer)
        self.include_issuer.toggled.connect(self._on_param_changed)
        controls.addWidget(self.include_issuer, 2, 1)

        self.include_date = QCheckBox("Date")
        self.include_date.setChecked(self.profile.include_date)
        self.include_date.toggled.connect(self._on_param_changed)
        controls.addWidget(self.include_date, 2, 2)

        self.include_reason = QCheckBox("Reason")
        self.include_reason.setChecked(self.profile.include_reason)
        self.include_reason.toggled.connect(self._on_param_changed)
        controls.addWidget(self.include_reason, 2, 3)

        layout.addLayout(controls)

        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(800, 500)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background: white;")
        layout.addWidget(self.preview_label)

        coords = QHBoxLayout()
        coords.addWidget(QLabel("X (mm):"))
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(0, 500)
        self.x_spin.setDecimals(1)
        self.x_spin.valueChanged.connect(self._on_coord_changed)
        coords.addWidget(self.x_spin)

        coords.addWidget(QLabel("Y (mm):"))
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(0, 500)
        self.y_spin.setDecimals(1)
        self.y_spin.valueChanged.connect(self._on_coord_changed)
        coords.addWidget(self.y_spin)

        coords.addStretch()
        layout.addLayout(coords)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply Position")
        apply_btn.clicked.connect(self._apply_position)
        btn_row.addWidget(apply_btn)

        reset_btn = QPushButton("Reset to Corner")
        reset_btn.clicked.connect(self._reset_position)
        btn_row.addWidget(reset_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._update_preview()

    def _on_param_changed(self):
        self.profile.width_mm = self.width_spin.value()
        self.profile.height_mm = self.height_spin.value()
        self.profile.font_size = self.font_spin.value()
        self.profile.position = self.position_combo.currentText()
        self.profile.include_owner = self.include_owner.isChecked()
        self.profile.include_issuer = self.include_issuer.isChecked()
        self.profile.include_date = self.include_date.isChecked()
        self.profile.include_reason = self.include_reason.isChecked()
        self._update_preview()

    def _on_coord_changed(self):
        self.stamp_x = self.x_spin.value()
        self.stamp_y = self.y_spin.value()
        self._update_preview()

    def _apply_position(self):
        self.profile.use_custom_position = True
        self.profile.custom_x = self.stamp_x * 72.0 / 25.4
        self.profile.custom_y = self.stamp_y * 72.0 / 25.4
        self.stamp_position_changed.emit(self.stamp_x, self.stamp_y)

    def _reset_position(self):
        self.profile.use_custom_position = False
        self.profile.position = self.position_combo.currentText()
        self.stamp_x = 0
        self.stamp_y = 0
        self.x_spin.setValue(0)
        self.y_spin.setValue(0)
        self._update_preview()

    def _update_preview(self):
        w = self.preview_label.width()
        h = self.preview_label.height()
        if w < 10 or h < 10:
            return

        pixmap = QPixmap(w, h)
        pixmap.fill(QColor(255, 255, 255))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        page_rect = pixmap.rect().adjusted(20, 20, -20, -20)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(page_rect)

        font = QFont("DejaVu Sans", 8)
        painter.setFont(font)
        painter.setPen(QColor(100, 100, 100))
        text_rect = page_rect.adjusted(10, 10, -10, -10)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop,
                         "Sample PDF content area...\nText blocks for reference")

        mm_to_px = min(w, h) / 297.0
        stamp_w = int(self.profile.width_mm * mm_to_px)
        stamp_h = int(self.profile.height_mm * mm_to_px)

        if self.profile.use_custom_position:
            sx = int(self.stamp_x * mm_to_px) + 20
            sy = h - int(self.stamp_y * mm_to_px) - stamp_h - 20
        else:
            pos = self.position_combo.currentText()
            margin = int(36 * mm_to_px)
            if "right" in pos:
                sx = page_rect.right() - stamp_w - margin
            else:
                sx = page_rect.left() + margin
            if "top" in pos:
                sy = page_rect.top() + margin
            else:
                sy = page_rect.bottom() - stamp_h - margin

        stamp_rect = (sx, sy, stamp_w, stamp_h)
        blue = QColor(0, 74, 173)
        painter.setPen(QPen(blue, 2))
        painter.setBrush(QColor(240, 245, 255, 200))
        painter.drawRoundedRect(stamp_rect[0], stamp_rect[1], stamp_rect[2], stamp_rect[3], 4, 4)

        text_font = QFont("DejaVu Sans", max(6, int(self.profile.font_size * 0.6)))
        painter.setFont(text_font)
        painter.setPen(blue)

        lines = ["Digitally signed by:"]
        if self.cert_name:
            lines.append(self.cert_name)
        if self.include_date.isChecked():
            lines.append(time.strftime("%d.%m.%Y"))
        if self.include_reason.isChecked() and self.reason:
            lines.append(f"Reason: {self.reason}")
        if self.include_issuer.isChecked():
            lines.append("Issuer: ...")

        text_y = stamp_rect[1] + 8
        text_x = stamp_rect[0] + 6
        max_text_w = stamp_rect[2] - 12
        for line in lines:
            painter.drawText(text_x, text_y, max_text_w, 16, Qt.TextSingleLine, line)
            text_y += 14

        painter.end()
        self.preview_label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            stamp_rect = self._get_stamp_rect()
            if stamp_rect and stamp_rect.contains(event.pos()):
                self.dragging = True
                self.drag_offset = event.pos() - QPoint(stamp_rect[0], stamp_rect[1])

    def mouseMoveEvent(self, event):
        if self.dragging:
            pos = event.pos() - self.drag_offset
            mm_to_px = min(self.preview_label.width(), self.preview_label.height()) / 297.0
            self.stamp_x = max(0, (pos.x() - 20) / mm_to_px)
            self.stamp_y = max(0, (self.preview_label.height() - pos.y() - int(self.profile.height_mm * mm_to_px) - 20) / mm_to_px)
            self.x_spin.setValue(self.stamp_x)
            self.y_spin.setValue(self.stamp_y)
            self._update_preview()

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def _get_stamp_rect(self):
        w = self.preview_label.width()
        h = self.preview_label.height()
        mm_to_px = min(w, h) / 297.0
        stamp_w = int(self.profile.width_mm * mm_to_px)
        stamp_h = int(self.profile.height_mm * mm_to_px)
        sx = int(self.stamp_x * mm_to_px) + 20
        sy = h - int(self.stamp_y * mm_to_px) - stamp_h - 20
        return (sx, sy, stamp_w, stamp_h)
