import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from pdfsigner.gui import MainWindow
from pdfsigner.applog import log_info
from pdfsigner import APP_VERSION


def _find_icon():
    candidates = [
        os.path.join(os.path.dirname(__file__), "app-icon.png"),
        os.path.join(os.path.dirname(__file__), "..", "app-icon.png"),
        "/usr/share/pixmaps/pdfsigner.png",
        os.path.expanduser("~/.local/share/icons/pdfsigner.png"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def main():
    log_info(f"Application started. Version {APP_VERSION}")
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Signer Linux")
    app.setApplicationVersion(APP_VERSION)
    icon_path = _find_icon()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    window = MainWindow()
    if icon_path:
        window.setWindowIcon(QIcon(icon_path))
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
