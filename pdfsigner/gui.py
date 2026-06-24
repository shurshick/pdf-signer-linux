import json
import os
import subprocess
import sys
import time
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QMessageBox, QProgressBar, QGroupBox, QListWidget, QTextEdit,
    QSplitter, QTabWidget, QSpinBox, QDoubleSpinBox, QSlider,
    QFormLayout, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QToolTip,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QFont, QIcon, QDesktopServices, QKeySequence

from pdfsigner import APP_VERSION, APP_NAME, APP_PROJECT_URL, APP_COPYRIGHT
from pdfsigner.i18n import t
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
from pdfsigner.stamp_editor import StampPreviewDialog
from pdfsigner.diagnostics import run_diagnostics, format_report
from pdfsigner.applog import log_info, log_error


class SignThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, files, cert, profile, reason, output_dir, save_next_to, verify_after, detached_mode):
        super().__init__()
        self.files = files
        self.cert = cert
        self.profile = profile
        self.reason = reason
        self.output_dir = output_dir
        self.save_next_to = save_next_to
        self.verify_after = verify_after
        self.detached_mode = detached_mode

    def run(self):
        results = []
        try:
            for i, pdf_path in enumerate(self.files):
                self.progress.emit(i + 1, len(self.files), pdf_path)

                output_dir = os.path.dirname(pdf_path) if self.save_next_to else self.output_dir
                os.makedirs(output_dir, exist_ok=True)

                base = os.path.splitext(os.path.basename(pdf_path))[0]
                output_pdf = os.path.join(output_dir, f"{base}-signed.pdf")
                counter = 2
                while os.path.exists(output_pdf):
                    output_pdf = os.path.join(output_dir, f"{base}-signed-{counter}.pdf")
                    counter += 1

                sig_path = output_pdf + ".sig"

                if self.detached_mode:
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
                        result = f"{os.path.basename(pdf_path)}\nSigning failed: {e}"
                else:
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
                        signature_fn="embedded",
                        profile=self.profile,
                    )
                    apply_stamp(pdf_path, output_pdf, stamp_path, self.profile.pages, self.profile)
                    os.remove(stamp_path)

                    try:
                        sign_embedded(output_pdf, self.cert, output_pdf)
                        result = f"{os.path.basename(pdf_path)} -> {os.path.basename(output_pdf)}\nSignature: embedded"
                    except Exception as e:
                        result = f"{os.path.basename(pdf_path)}\nSigning failed: {e}"

                if self.verify_after:
                    if self.detached_mode and os.path.exists(sig_path):
                        vr = verify_signature(sig_path)
                    elif not self.detached_mode and os.path.exists(output_pdf):
                        vr = verify_signature(output_pdf)
                    else:
                        vr = {"status": "SKIPPED"}
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
        self.setMinimumSize(900, 650)
        self._init_ui()
        self._load_certs()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)

        files_group = QGroupBox(t("files"))
        files_layout = QVBoxLayout()
        btn_row = QHBoxLayout()
        add_btn = QPushButton(t("add_files"))
        add_btn.clicked.connect(self._add_files)
        remove_btn = QPushButton(t("remove_file"))
        remove_btn.clicked.connect(self._remove_file)
        clear_btn = QPushButton(t("clear"))
        clear_btn.clicked.connect(self._clear_files)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        files_layout.addLayout(btn_row)

        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(100)
        self.file_list.setDragDropMode(QListWidget.NoDragDrop)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.itemDoubleClicked.connect(self._on_file_double_click)
        self.file_list.setToolTip(t("select_pdf"))
        files_layout.addWidget(self.file_list)

        self.file_summary = QLabel(t("select_pdf"))
        files_layout.addWidget(self.file_summary)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        cert_group = QGroupBox(t("certificate"))
        cert_layout = QVBoxLayout()

        self.cert_table = QTableWidget()
        self.cert_table.setColumnCount(5)
        self.cert_table.setHorizontalHeaderLabels([
            t("cn"), t("store"), t("valid_to"), t("thumbprint"), t("private_key")
        ])
        self.cert_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cert_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.cert_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cert_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.cert_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.cert_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cert_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.cert_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cert_table.verticalHeader().setVisible(False)
        self.cert_table.setMaximumHeight(140)
        self.cert_table.clicked.connect(self._on_cert_clicked)
        cert_layout.addWidget(self.cert_table)

        cert_btn_row = QHBoxLayout()
        refresh_btn = QPushButton(t("refresh"))
        refresh_btn.clicked.connect(self._load_certs)
        cert_btn_row.addWidget(refresh_btn)
        cert_btn_row.addStretch()
        cert_layout.addLayout(cert_btn_row)

        cert_group.setLayout(cert_layout)
        layout.addWidget(cert_group)

        options_group = QGroupBox(t("options"))
        opt_layout = QGridLayout()

        opt_layout.addWidget(QLabel(t("output_folder")), 0, 0)
        self.output_dir = QLineEdit(os.path.expanduser("~/Documents/Signed PDFs"))
        opt_layout.addWidget(self.output_dir, 0, 1)
        browse_btn = QPushButton(t("browse"))
        browse_btn.clicked.connect(self._browse_output)
        opt_layout.addWidget(browse_btn, 0, 2)

        opt_layout.addWidget(QLabel(t("signing_reason")), 1, 0)
        self.reason = QLineEdit(t("default_reason"))
        opt_layout.addWidget(self.reason, 1, 1, 1, 2)

        opt_layout.addWidget(QLabel(t("stamp_profile")), 2, 0)
        self.profile_select = QComboBox()
        self.profile_select.addItems([t("minimal"), t("standard"), t("detailed")])
        self.profile_select.setCurrentText(t(self.settings.stamp_profile.name))
        self.profile_select.currentTextChanged.connect(self._on_profile_change)
        opt_layout.addWidget(self.profile_select, 2, 1)

        opt_layout.addWidget(QLabel(t("position")), 3, 0)
        self.position_select = QComboBox()
        self.position_select.addItems([t("bottom_right"), t("bottom_left"), t("top_right"), t("top_left")])
        self.position_select.setCurrentText(t(self.settings.stamp_profile.position))
        opt_layout.addWidget(self.position_select, 3, 1)

        opt_layout.addWidget(QLabel(t("pages")), 4, 0)
        self.page_select = QComboBox()
        self.page_select.addItems(["All pages", "First page", "Last page", "Specific page"])
        self.page_select.currentTextChanged.connect(self._on_page_select_changed)
        opt_layout.addWidget(self.page_select, 4, 1)

        self.specific_page_spin = QSpinBox()
        self.specific_page_spin.setRange(1, 9999)
        self.specific_page_spin.setValue(1)
        self.specific_page_spin.setEnabled(False)
        opt_layout.addWidget(self.specific_page_spin, 4, 2)

        self.auto_place_check = QCheckBox(t("auto_place"))
        self.auto_place_check.setChecked(self.settings.stamp_profile.auto_place)
        opt_layout.addWidget(self.auto_place_check, 5, 0, 1, 2)

        self.custom_pos_check = QCheckBox(t("use_custom_pos"))
        self.custom_pos_check.setChecked(self.settings.stamp_profile.use_custom_position)
        self.custom_pos_check.toggled.connect(self._on_custom_pos_toggled)
        opt_layout.addWidget(self.custom_pos_check, 6, 0, 1, 2)

        opt_layout.addWidget(QLabel(t("custom_x_mm")), 7, 0)
        self.custom_x_spin = QDoubleSpinBox()
        self.custom_x_spin.setRange(0, 1000)
        self.custom_x_spin.setSuffix(" mm")
        self.custom_x_spin.setValue(self.settings.stamp_profile.custom_x * 25.4 / 72.0)
        self.custom_x_spin.setEnabled(self.settings.stamp_profile.use_custom_position)
        opt_layout.addWidget(self.custom_x_spin, 7, 1)

        opt_layout.addWidget(QLabel(t("custom_y_mm")), 8, 0)
        self.custom_y_spin = QDoubleSpinBox()
        self.custom_y_spin.setRange(0, 1000)
        self.custom_y_spin.setSuffix(" mm")
        self.custom_y_spin.setValue(self.settings.stamp_profile.custom_y * 25.4 / 72.0)
        self.custom_y_spin.setEnabled(self.settings.stamp_profile.use_custom_position)
        opt_layout.addWidget(self.custom_y_spin, 8, 1)

        stamp_editor_btn = QPushButton("Stamp Editor")
        stamp_editor_btn.clicked.connect(self._open_stamp_editor)
        opt_layout.addWidget(stamp_editor_btn, 8, 2)

        logo_row = QHBoxLayout()
        logo_row.addWidget(QLabel(t("logo")))
        self.logo_path_edit = QLineEdit(self.settings.stamp_profile.logo_path)
        self.logo_path_edit.setReadOnly(True)
        logo_row.addWidget(self.logo_path_edit)
        logo_browse_btn = QPushButton(t("browse_logo"))
        logo_browse_btn.clicked.connect(self._browse_logo)
        logo_row.addWidget(logo_browse_btn)
        opt_layout.addLayout(logo_row, 9, 0, 1, 3)

        opt_layout.addWidget(QLabel(t("logo_scale")), 10, 0)
        self.logo_scale_spin = QSpinBox()
        self.logo_scale_spin.setRange(50, 300)
        self.logo_scale_spin.setValue(self.settings.stamp_profile.logo_scale)
        self.logo_scale_spin.setSuffix("%")
        opt_layout.addWidget(self.logo_scale_spin, 10, 1)

        self.save_next = QCheckBox(t("save_next_to"))
        self.save_next.setChecked(True)
        opt_layout.addWidget(self.save_next, 11, 0, 1, 3)

        self.verify_after = QCheckBox(t("verify_after"))
        self.verify_after.setChecked(self.settings.verify_after_signing)
        opt_layout.addWidget(self.verify_after, 12, 0, 1, 3)

        self.detached_check = QCheckBox(t("detached_sig"))
        self.detached_check.setChecked(True)
        opt_layout.addWidget(self.detached_check, 13, 0, 1, 3)

        export_btn = QPushButton(t("export_settings"))
        export_btn.clicked.connect(self._export_settings)
        opt_layout.addWidget(export_btn, 14, 0)

        import_btn = QPushButton(t("import_settings"))
        import_btn.clicked.connect(self._import_settings)
        opt_layout.addWidget(import_btn, 14, 1)

        options_group.setLayout(opt_layout)
        layout.addWidget(options_group)

        action_layout = QHBoxLayout()
        sign_btn = QPushButton(t("sign"))
        sign_btn.clicked.connect(self._sign)
        sign_btn.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        action_layout.addWidget(sign_btn)

        verify_btn = QPushButton(t("verify_btn"))
        verify_btn.clicked.connect(self._verify_files)
        action_layout.addWidget(verify_btn)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(1)
        action_layout.addWidget(self.progress)

        diag_btn = QPushButton(t("diagnostics"))
        diag_btn.clicked.connect(self._open_diagnostics)
        action_layout.addWidget(diag_btn)

        about_btn = QPushButton(t("about"))
        about_btn.clicked.connect(self._open_about)
        action_layout.addWidget(about_btn)

        layout.addLayout(action_layout)

        self.status_label = QLabel(t("ready"))
        layout.addWidget(self.status_label)

        self.file_list.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.file_list and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Delete:
                self._remove_file()
                return True
            if event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
                self.file_list.selectAll()
                return True
        return super().eventFilter(obj, event)

    def _on_file_double_click(self, item):
        row = self.file_list.row(item)
        if 0 <= row < len(self.pdf_files):
            file_path = self.pdf_files[row]
            directory = os.path.dirname(file_path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(directory))

    def _on_custom_pos_toggled(self, checked):
        self.custom_x_spin.setEnabled(checked)
        self.custom_y_spin.setEnabled(checked)
        if checked:
            self.auto_place_check.setChecked(False)

    def _browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("browse_logo"), "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All files (*.*)"
        )
        if path:
            size = os.path.getsize(path)
            if size > 1024 * 1024:
                QMessageBox.warning(self, t("stamp_warning"), "Logo file exceeds 1 MB limit.")
                return
            self.logo_path_edit.setText(path)

    def _load_certs(self):
        self.cert_table.setRowCount(0)
        self.selected_cert = None
        self.status_label.setText(t("loading_certs"))
        try:
            certs = load_certificates()
            self.cert_table.setRowCount(len(certs))
            for row, cert in enumerate(certs):
                self.cert_table.setItem(row, 0, QTableWidgetItem(cert.subject_cn))
                self.cert_table.setItem(row, 1, QTableWidgetItem("uMy"))
                self.cert_table.setItem(row, 2, QTableWidgetItem(""))
                thumb_text = cert.thumbprint[:16] + "..." if len(cert.thumbprint) > 16 else cert.thumbprint
                self.cert_table.setItem(row, 3, QTableWidgetItem(thumb_text))
                pk_text = t("has_private_key") if cert.has_private_key else t("no_private_key")
                pk_item = QTableWidgetItem(pk_text)
                if not cert.has_private_key:
                    pk_item.setForeground(Qt.red)
                self.cert_table.setItem(row, 4, pk_item)
                self.cert_table.item(row, 0).setData(Qt.UserRole, cert)
            self.status_label.setText(t("found_certs", count=len(certs)))
            if len(certs) > 0:
                self.cert_table.selectRow(0)
                self._on_cert_clicked(self.cert_table.model().index(0, 0))
        except Exception as e:
            self.status_label.setText(t("error_loading_certs", error=str(e)))

    def _on_cert_clicked(self, index):
        row = index.row()
        item = self.cert_table.item(row, 0)
        if item:
            self.selected_cert = item.data(Qt.UserRole)
            if self.selected_cert:
                self.status_label.setText(f"{t('owner')} {self.selected_cert.subject_cn} | {t('issuer')} {self.selected_cert.issuer_cn}")
                if not self.selected_cert.has_private_key:
                    QMessageBox.warning(self, t("stamp_warning"), t("cert_no_key"))

    def _on_profile_change(self, name):
        profile_map = {t("minimal"): "minimal", t("standard"): "standard", t("detailed"): "detailed"}
        profile_name = profile_map.get(name, name)
        if profile_name in BUILT_IN_PROFILES:
            p = BUILT_IN_PROFILES[profile_name]
            self.settings.stamp_profile = StampProfile.from_dict(p.to_dict())

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, t("select_pdf"), "", t("pdf_filter")
        )
        for f in files:
            if f not in self.pdf_files:
                self.pdf_files.append(f)
                self.file_list.addItem(os.path.basename(f))
                item = self.file_list.item(self.file_list.count() - 1)
                item.setToolTip(f)
        self._update_file_summary()

    def _remove_file(self):
        row = self.file_list.currentRow()
        if row >= 0:
            self.file_list.takeItem(row)
            self.pdf_files.pop(row)
            self._update_file_summary()

    def _clear_files(self):
        self.pdf_files.clear()
        self.file_list.clear()
        self._update_file_summary()

    def _update_file_summary(self):
        count = len(self.pdf_files)
        if count == 0:
            self.file_summary.setText(t("select_pdf"))
        else:
            total = sum(os.path.getsize(f) for f in self.pdf_files if os.path.exists(f))
            self.file_summary.setText(t("file_count", count=count, size=self._format_size(total)))

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _browse_output(self):
        d = QFileDialog.getExistingDirectory(self, t("select_output"))
        if d:
            self.output_dir.setText(d)

    def _export_settings(self):
        path, _ = QFileDialog.getSaveFileName(
            self, t("export_settings"), "settings.json", "JSON (*.json)"
        )
        if path:
            self._sync_profile_to_settings()
            export_settings(path, self.settings)
            QMessageBox.information(self, t("export_settings"), t("settings_exported"))

    def _import_settings(self):
        path, _ = QFileDialog.getOpenFileName(
            self, t("import_settings"), "", "JSON (*.json)"
        )
        if path:
            try:
                imported = import_settings(path)
                self.settings = imported
                save_settings(self.settings)
                self._apply_settings_to_ui()
                QMessageBox.information(self, t("import_settings"), t("settings_imported"))
            except Exception as e:
                QMessageBox.critical(self, t("error"), str(e))

    def _on_page_select_changed(self, text):
        self.specific_page_spin.setEnabled(text == "Specific page")

    def _get_pages_str(self):
        choice = self.page_select.currentText()
        if choice == "First page":
            return "1"
        elif choice == "Last page":
            return "1-"
        elif choice == "Specific page":
            n = self.specific_page_spin.value()
            return str(n)
        return "1-"

    def _apply_settings_to_ui(self):
        self.verify_after.setChecked(self.settings.verify_after_signing)
        p = self.settings.stamp_profile
        self.position_select.setCurrentText(t(p.position.replace("-", "_")))
        self.auto_place_check.setChecked(p.auto_place)
        self.custom_pos_check.setChecked(p.use_custom_position)
        self.custom_x_spin.setValue(p.custom_x * 25.4 / 72.0)
        self.custom_y_spin.setValue(p.custom_y * 25.4 / 72.0)
        self.logo_path_edit.setText(p.logo_path)
        self.logo_scale_spin.setValue(p.logo_scale)

    def _sync_profile_to_settings(self):
        position_map = {
            t("bottom_right"): "bottom-right",
            t("bottom_left"): "bottom-left",
            t("top_right"): "top-right",
            t("top_left"): "top-left",
        }
        self.settings.stamp_profile.position = position_map.get(
            self.position_select.currentText(), "bottom-right"
        )
        self.settings.stamp_profile.pages = self._get_pages_str()
        self.settings.stamp_profile.auto_place = self.auto_place_check.isChecked()
        self.settings.stamp_profile.use_custom_position = self.custom_pos_check.isChecked()
        self.settings.stamp_profile.custom_x = self.custom_x_spin.value() * 72.0 / 25.4
        self.settings.stamp_profile.custom_y = self.custom_y_spin.value() * 72.0 / 25.4
        self.settings.stamp_profile.logo_path = self.logo_path_edit.text()
        self.settings.stamp_profile.logo_scale = self.logo_scale_spin.value()

    def _get_profile(self) -> StampProfile:
        self._sync_profile_to_settings()
        p = StampProfile.from_dict(self.settings.stamp_profile.to_dict())
        p.normalize()
        return p

    def _sign(self):
        if not self.pdf_files:
            QMessageBox.warning(self, t("error"), t("no_files"))
            return
        if not self.selected_cert:
            QMessageBox.warning(self, t("error"), t("no_certificate"))
            return

        self.progress.setMaximum(len(self.pdf_files))
        self.progress.setValue(0)
        self.status_label.setText(t("signing"))

        profile = self._get_profile()
        self.settings.verify_after_signing = self.verify_after.isChecked()
        self.settings.stamp_profile = profile
        save_settings(self.settings)

        self.thread = SignThread(
            self.pdf_files, self.selected_cert, profile,
            self.reason.text(), self.output_dir.text(),
            self.save_next.isChecked(), self.verify_after.isChecked(),
            self.detached_check.isChecked(),
        )
        self.thread.progress.connect(self._on_progress)
        self.thread.finished.connect(self._on_sign_done)
        self.thread.error.connect(self._on_sign_error)
        self.thread.start()

    def _on_progress(self, current, total, path):
        self.progress.setValue(current)
        self.status_label.setText(t("signing_progress", current=current, total=total, file=os.path.basename(path)))

    def _on_sign_done(self, results):
        self.progress.setValue(self.progress.maximum())
        self.status_label.setText(t("done"))
        log_info(f"Signing completed: {len(results)} file(s)")
        QMessageBox.information(
            self, t("done"),
            t("processed_files", count=len(results)) + "\n\n" + "\n\n".join(results),
        )

    def _on_sign_error(self, error):
        self.progress.setValue(0)
        self.status_label.setText(f"{t('error')}: {error}")
        log_error("Signing failed", Exception(error))
        QMessageBox.critical(self, t("error"), f"{t('signing_failed')}\n{error}")

    def _open_about(self):
        text = (
            f"{APP_NAME}\n"
            f"{t('version')}: {APP_VERSION}\n"
            f"{APP_COPYRIGHT}\n\n"
            f"{t('project')}: {APP_PROJECT_URL}\n\n"
            f"License: AGPL-3.0-or-later"
        )
        QMessageBox.about(self, t("about_title"), text)

    def _verify_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select files to verify", "",
            "PDF files and signatures (*.pdf *.sig);;All files (*.*)"
        )
        if not paths:
            return
        reports = []
        for p in paths:
            reports.append(verify_signature(p))
        report_text = format_verification_report(reports)
        QMessageBox.information(self, "Verification Result", report_text)

    def _open_diagnostics(self):
        report = run_diagnostics(APP_VERSION)
        text = format_report(report)
        QMessageBox.information(self, "Diagnostics", text)

    def _open_stamp_editor(self):
        profile = self._get_profile()
        cert_name = self.selected_cert.subject_cn if self.selected_cert else ""
        reason = self.reason.text()
        dialog = StampPreviewDialog(profile, cert_name, reason, self)
        dialog.exec_()
        self.profile_select.setCurrentText(t(profile.name))
        self.position_select.setCurrentText(t(profile.position.replace("-", "_")))
