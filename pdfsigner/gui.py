import json
import os
import time
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QMessageBox, QProgressBar, QGroupBox, QListWidget, QTextEdit,
    QSplitter, QTabWidget, QSpinBox, QDoubleSpinBox, QSlider,
    QFormLayout, QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from pdfsigner import APP_VERSION, APP_NAME, APP_PROJECT_URL, APP_COPYRIGHT
from pdfsigner.settings import (
    ApplicationSettings, StampProfile, BUILT_IN_PROFILES,
    load_settings, save_settings, export_settings, import_settings,
)
from pdfsigner.certstore import CertInfo, load_certificates
from pdfsigner.signer import sign_detached, sign_embedded, verify_signature, format_verification_report
from pdfsigner.stamp import (
    create_stamp_image, validate_stamp_size, build_stamp_text,
)
from pdfsigner.pdfstamp import apply_stamp
from pdfsigner.diagnostics import run_diagnostics, format_report
from pdfsigner.applog import log_info, log_error


class SignThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, files, cert, profile, reason, output_dir, save_next_to, verify_after):
        super().__init__()
        self.files = files
        self.cert = cert
        self.profile = profile
        self.reason = reason
        self.output_dir = output_dir
        self.save_next_to = save_next_to
        self.verify_after = verify_after

    def run(self):
        results = []
        try:
            from pdfsigner.signer import sign_detached
            for i, pdf_path in enumerate(self.files):
                self.progress.emit(i + 1, len(self.files), pdf_path)

                output_dir = os.path.dirname(pdf_path) if self.save_next_to else self.output_dir
                os.makedirs(output_dir, exist_ok=True)

                base = os.path.splitext(os.path.basename(pdf_path))[0]
                output_pdf = os.path.join(output_dir, f"{base}_stamped.pdf")
                counter = 2
                while os.path.exists(output_pdf):
                    output_pdf = os.path.join(output_dir, f"{base}_stamped_{counter}.pdf")
                    counter += 1

                sig_path = output_pdf + ".sig"

                stamp_path = output_pdf + ".stamp.png"
                create_stamp_image(
                    stamp_path,
                    owner=self.cert.subject_cn,
                    issuer=self.cert.issuer_cn,
                    serial=self.cert.serial,
                    thumbprint=self.cert.thumbprint,
                    reason=self.reason,
                    valid_from=time.strftime("%d.%m.%Y"),
                    valid_to=time.strftime("%d.%m.%Y"),
                    signature_fn=os.path.basename(sig_path),
                    profile=self.profile,
                )

                apply_stamp(pdf_path, output_pdf, stamp_path, self.profile.pages, self.profile)
                os.remove(stamp_path)

                try:
                    sign_detached(output_pdf, self.cert, sig_path)
                    result = f"{os.path.basename(pdf_path)} -> {os.path.basename(output_pdf)}\nSignature: {os.path.basename(sig_path)}"
                except Exception as e:
                    result = f"{os.path.basename(pdf_path)} -> {os.path.basename(output_pdf)}\nSigning failed: {e}"

                if self.verify_after and os.path.exists(sig_path):
                    vr = verify_signature(sig_path)
                    result += f"\nVerification: {vr['status']}"

                results.append(result)

            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.pdf_files = []
        self.selected_cert = None
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(900, 600)
        self._init_ui()
        self._load_certs()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        files_group = QGroupBox("PDF Files")
        files_layout = QVBoxLayout()
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add PDFs")
        add_btn.clicked.connect(self._add_files)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_files)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(clear_btn)
        files_layout.addLayout(btn_row)
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(100)
        files_layout.addWidget(self.file_list)
        self.file_summary = QLabel("Selected PDFs: 0")
        files_layout.addWidget(self.file_summary)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        options_group = QGroupBox("Options")
        opt_layout = QGridLayout()

        opt_layout.addWidget(QLabel("Output folder:"), 0, 0)
        self.output_dir = QLineEdit(os.path.expanduser("~/Documents/Signed PDFs"))
        opt_layout.addWidget(self.output_dir, 0, 1)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_output)
        opt_layout.addWidget(browse_btn, 0, 2)

        self.save_next = QCheckBox("Save next to source PDF")
        self.save_next.setChecked(True)
        opt_layout.addWidget(self.save_next, 1, 0, 1, 3)

        self.verify_after = QCheckBox("Verify after signing")
        self.verify_after.setChecked(self.settings.verify_after_signing)
        opt_layout.addWidget(self.verify_after, 2, 0, 1, 3)

        opt_layout.addWidget(QLabel("Signing reason:"), 3, 0)
        self.reason = QLineEdit("Signed with PDF Signer Linux")
        opt_layout.addWidget(self.reason, 3, 1, 1, 2)

        opt_layout.addWidget(QLabel("Scale:"), 4, 0)
        self.scale = QLineEdit(str(self.settings.stamp_profile.scale))
        opt_layout.addWidget(self.scale, 4, 1)

        opt_layout.addWidget(QLabel("Stamp profile:"), 5, 0)
        self.profile_select = QComboBox()
        self.profile_select.addItems(["minimal", "standard", "detailed"])
        self.profile_select.setCurrentText(self.settings.stamp_profile.name)
        self.profile_select.currentTextChanged.connect(self._on_profile_change)
        opt_layout.addWidget(self.profile_select, 5, 1)

        options_group.setLayout(opt_layout)
        layout.addWidget(options_group)

        cert_group = QGroupBox("Certificate")
        cert_layout = QVBoxLayout()
        self.cert_combo = QComboBox()
        self.cert_combo.currentTextChanged.connect(self._on_cert_change)
        cert_layout.addWidget(self.cert_combo)
        self.cert_info = QLabel("No certificate selected")
        self.cert_info.setWordWrap(True)
        cert_layout.addWidget(self.cert_info)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_certs)
        cert_layout.addWidget(refresh_btn)
        cert_group.setLayout(cert_layout)
        layout.addWidget(cert_group)

        action_layout = QHBoxLayout()
        sign_btn = QPushButton("Sign and Stamp")
        sign_btn.clicked.connect(self._sign)
        sign_btn.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        action_layout.addWidget(sign_btn)

        verify_btn = QPushButton("Verify Signature")
        verify_btn.clicked.connect(self._verify)
        action_layout.addWidget(verify_btn)

        stamp_btn = QPushButton("Stamp Editor")
        stamp_btn.clicked.connect(self._open_stamp_editor)
        action_layout.addWidget(stamp_btn)

        diag_btn = QPushButton("Diagnostics")
        diag_btn.clicked.connect(self._open_diagnostics)
        action_layout.addWidget(diag_btn)

        about_btn = QPushButton("About")
        about_btn.clicked.connect(self._open_about)
        action_layout.addWidget(about_btn)

        layout.addLayout(action_layout)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

    def _load_certs(self):
        self.cert_combo.clear()
        self.status_label.setText("Loading certificates...")
        try:
            certs = load_certificates()
            for c in certs:
                self.cert_combo.addItem(c.display_name, c)
            self.status_label.setText(f"Found {len(certs)} certificate(s)")
        except Exception as e:
            self.status_label.setText(f"Error loading certificates: {e}")

    def _on_cert_change(self, text):
        idx = self.cert_combo.currentIndex()
        if idx >= 0:
            self.selected_cert = self.cert_combo.itemData(idx)
            if self.selected_cert:
                self.cert_info.setText(
                    f"Owner: {self.selected_cert.subject_cn}\n"
                    f"Issuer: {self.selected_cert.issuer_cn}\n"
                    f"Serial: {self.selected_cert.serial}\n"
                    f"SHA1: {self.selected_cert.thumbprint}"
                )

    def _on_profile_change(self, name):
        if name in BUILT_IN_PROFILES:
            p = BUILT_IN_PROFILES[name]
            self.settings.stamp_profile = StampProfile.from_dict(p.to_dict())
            self.scale.setText(str(p.scale))

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF files", "", "PDF files (*.pdf);;All files (*.*)"
        )
        for f in files:
            if f not in self.pdf_files:
                self.pdf_files.append(f)
                self.file_list.addItem(os.path.basename(f))
        self.file_summary.setText(f"Selected PDFs: {len(self.pdf_files)}")

    def _clear_files(self):
        self.pdf_files.clear()
        self.file_list.clear()
        self.file_summary.setText("Selected PDFs: 0")

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select output folder")
        if d:
            self.output_dir.setText(d)

    def _get_profile(self) -> StampProfile:
        p = StampProfile.from_dict(self.settings.stamp_profile.to_dict())
        try:
            p.scale = float(self.scale.text())
        except ValueError:
            pass
        p.normalize()
        return p

    def _sign(self):
        if not self.pdf_files:
            QMessageBox.warning(self, "Error", "Add at least one PDF file.")
            return
        if not self.selected_cert:
            QMessageBox.warning(self, "Error", "Select a certificate.")
            return

        self.progress.setMaximum(len(self.pdf_files))
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.status_label.setText("Signing...")

        profile = self._get_profile()
        self.settings.verify_after_signing = self.verify_after.isChecked()
        self.settings.stamp_profile = profile
        save_settings(self.settings)

        self.thread = SignThread(
            self.pdf_files, self.selected_cert, profile,
            self.reason.text(), self.output_dir.text(),
            self.save_next.isChecked(), self.verify_after.isChecked(),
        )
        self.thread.progress.connect(self._on_progress)
        self.thread.finished.connect(self._on_sign_done)
        self.thread.error.connect(self._on_sign_error)
        self.thread.start()

    def _on_progress(self, current, total, path):
        self.progress.setValue(current)
        self.status_label.setText(f"Signing {current}/{total}: {os.path.basename(path)}")

    def _on_sign_done(self, results):
        self.progress.setVisible(False)
        self.status_label.setText("Done")
        log_info(f"Signing completed: {len(results)} file(s)")
        QMessageBox.information(
            self, "Done",
            f"Processed {len(results)} file(s)\n\n" + "\n\n".join(results),
        )

    def _on_sign_error(self, error):
        self.progress.setVisible(False)
        self.status_label.setText(f"Error: {error}")
        log_error("Signing failed", Exception(error))
        QMessageBox.critical(self, "Error", f"Signing failed:\n{error}")

    def _verify(self):
        if not self.pdf_files:
            QMessageBox.warning(self, "Error", "Add files to verify.")
            return
        reports = []
        for f in self.pdf_files:
            reports.append(verify_signature(f))
        report_text = format_verification_report(reports)
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Verification Report")
        dlg.setText(report_text[:2000])
        dlg.exec_()

    def _open_stamp_editor(self):
        dlg = StampEditorDialog(self.settings.stamp_profile, self)
        if dlg.exec_():
            self.settings.stamp_profile = dlg.profile
            save_settings(self.settings)

    def _open_diagnostics(self):
        report = run_diagnostics(APP_VERSION)
        text = format_report(report)
        dlg = QMessageBox(self)
        dlg.setWindowTitle("CryptoPro Diagnostics")
        dlg.setText(text[:2000])
        dlg.exec_()

    def _open_about(self):
        text = (
            f"{APP_NAME}\n"
            f"Version: {APP_VERSION}\n"
            f"{APP_COPYRIGHT}\n\n"
            f"Project: {APP_PROJECT_URL}\n\n"
            f"License: AGPL-3.0-or-later"
        )
        QMessageBox.about(self, "About", text)


class StampEditorDialog(QMessageBox):
    def __init__(self, profile: StampProfile, parent=None):
        super().__init__(parent)
        self.profile = StampProfile.from_dict(profile.to_dict())
        self.setWindowTitle("Stamp Editor")
        self.setMinimumSize(600, 500)

    def exec_(self):
        from PyQt5.QtWidgets import QDialog, QDialogButtonBox
        dlg = QDialog(self.parent())
        dlg.setWindowTitle("Stamp Editor")
        dlg.setMinimumSize(600, 500)

        layout = QVBoxLayout(dlg)

        form = QFormLayout()

        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["minimal", "standard", "detailed"])
        self.profile_combo.setCurrentText(self.profile.name)
        self.profile_combo.currentTextChanged.connect(self._load_builtin)
        form.addRow("Template:", self.profile_combo)

        self.pages = QLineEdit(self.profile.pages)
        form.addRow("Pages:", self.pages)

        self.position = QComboBox()
        self.position.addItems(["bottom-right", "bottom-left", "top-right", "top-left"])
        self.position.setCurrentText(self.profile.position)
        form.addRow("Position:", self.position)

        self.width = QDoubleSpinBox()
        self.width.setRange(40, 200)
        self.width.setValue(self.profile.width_mm)
        self.width.setSuffix(" mm")
        form.addRow("Width:", self.width)

        self.height = QDoubleSpinBox()
        self.height.setRange(15, 100)
        self.height.setValue(self.profile.height_mm)
        self.height.setSuffix(" mm")
        form.addRow("Height:", self.height)

        self.font_size = QDoubleSpinBox()
        self.font_size.setRange(4, 16)
        self.font_size.setValue(self.profile.font_size)
        self.font_size.setSuffix(" pt")
        form.addRow("Font size:", self.font_size)

        self.opacity = QSpinBox()
        self.opacity.setRange(10, 100)
        self.opacity.setValue(int(self.profile.opacity * 100))
        self.opacity.setSuffix(" %")
        form.addRow("Opacity:", self.opacity)

        self.include_owner = QCheckBox()
        self.include_owner.setChecked(self.profile.include_owner)
        form.addRow("Owner:", self.include_owner)

        self.include_issuer = QCheckBox()
        self.include_issuer.setChecked(self.profile.include_issuer)
        form.addRow("Issuer:", self.include_issuer)

        self.include_date = QCheckBox()
        self.include_date.setChecked(self.profile.include_date)
        form.addRow("Date:", self.include_date)

        self.include_reason = QCheckBox()
        self.include_reason.setChecked(self.profile.include_reason)
        form.addRow("Reason:", self.include_reason)

        self.include_serial = QCheckBox()
        self.include_serial.setChecked(self.profile.include_serial)
        form.addRow("Serial:", self.include_serial)

        self.include_validity = QCheckBox()
        self.include_validity.setChecked(self.profile.include_validity)
        form.addRow("Validity:", self.include_validity)

        layout.addLayout(form)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setMaximumHeight(120)
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(self.preview)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)

        self._update_preview()
        for w in [self.include_owner, self.include_issuer, self.include_date,
                  self.include_reason, self.include_serial, self.include_validity]:
            w.stateChanged.connect(self._update_preview)

        if dlg.exec_():
            self._save_from_controls()
            return True
        return False

    def _load_builtin(self, name):
        if name in BUILT_IN_PROFILES:
            p = BUILT_IN_PROFILES[name]
            self.profile = StampProfile.from_dict(p.to_dict())
            self.pages.setText(p.pages)
            self.position.setCurrentText(p.position)
            self.width.setValue(p.width_mm)
            self.height.setValue(p.height_mm)
            self.font_size.setValue(p.font_size)
            self.opacity.setValue(int(p.opacity * 100))
            self.include_owner.setChecked(p.include_owner)
            self.include_issuer.setChecked(p.include_issuer)
            self.include_date.setChecked(p.include_date)
            self.include_reason.setChecked(p.include_reason)
            self.include_serial.setChecked(p.include_serial)
            self.include_validity.setChecked(p.include_validity)
            self._update_preview()

    def _update_preview(self):
        text = build_stamp_text(
            StampProfile(
                include_owner=self.include_owner.isChecked(),
                include_issuer=self.include_issuer.isChecked(),
                include_date=self.include_date.isChecked(),
                include_reason=self.include_reason.isChecked(),
                include_serial=self.include_serial.isChecked(),
                include_validity=self.include_validity.isChecked(),
            ),
            owner="Preview User",
            issuer="Preview CA",
            serial="12345678",
            reason="Test reason",
            valid_from="01.01.2025",
            valid_to="01.01.2027",
        )
        self.preview.setText(text)

    def _save_from_controls(self):
        self.profile.name = self.profile_combo.currentText()
        self.profile.pages = self.pages.text()
        self.profile.position = self.position.currentText()
        self.profile.width_mm = self.width.value()
        self.profile.height_mm = self.height.value()
        self.profile.font_size = self.font_size.value()
        self.profile.opacity = self.opacity.value() / 100.0
        self.profile.include_owner = self.include_owner.isChecked()
        self.profile.include_issuer = self.include_issuer.isChecked()
        self.profile.include_date = self.include_date.isChecked()
        self.profile.include_reason = self.include_reason.isChecked()
        self.profile.include_serial = self.include_serial.isChecked()
        self.profile.include_validity = self.include_validity.isChecked()
        self.profile.normalize()
