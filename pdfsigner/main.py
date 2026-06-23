import sys
from PyQt5.QtWidgets import QApplication
from pdfsigner.gui import MainWindow
from pdfsigner.applog import log_info
from pdfsigner import APP_VERSION


def main():
    log_info(f"Application started. Version {APP_VERSION}")
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Signer Linux")
    app.setApplicationVersion(APP_VERSION)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
