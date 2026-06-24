#!/bin/bash
set -euo pipefail

APP_NAME="pdfsigner"
VERSION="${VERSION:-1.0.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
BUILDROOT="${ROOT_DIR}/.debbuild"
INSTALL_DIR="${BUILDROOT}/opt/${APP_NAME}"

echo "==> Checking project files"
for f in "${ROOT_DIR}/pyproject.toml" "${ROOT_DIR}/README.md"; do
    if [ ! -f "$f" ]; then
        echo "Error: $f not found"
        exit 1
    fi
done

echo "==> Cleaning previous build output"
rm -rf "${BUILDROOT}"
mkdir -p "${BUILDROOT}/DEBIAN" \
    "${BUILDROOT}/usr/bin" \
    "${BUILDROOT}/usr/share/applications" \
    "${BUILDROOT}/usr/share/icons/hicolor/256x256/apps" \
    "${BUILDROOT}/usr/share/doc/${APP_NAME}" \
    "${INSTALL_DIR}/lib" \
    "${DIST_DIR}"

echo "==> Installing Python package (pure Python only, no .so files)"
pip3 install --target "${INSTALL_DIR}/lib" --no-compile --no-deps "${ROOT_DIR}" 2>/dev/null || \
pip install --target "${INSTALL_DIR}/lib" --no-compile --no-deps "${ROOT_DIR}"

echo "==> Installing dependencies separately"
pip3 install --target "${INSTALL_DIR}/lib" --no-compile \
    pyhanko python-pkcs11 PyQt5 Pillow PyMuPDF cryptography 2>/dev/null || \
pip install --target "${INSTALL_DIR}/lib" --no-compile \
    pyhanko python-pkcs11 PyQt5 Pillow PyMuPDF cryptography

echo "==> Removing .so files that cause dependency issues"
find "${INSTALL_DIR}/lib" -name "*.so" -delete 2>/dev/null || true
find "${INSTALL_DIR}/lib" -name "*.so.*" -delete 2>/dev/null || true
find "${INSTALL_DIR}/lib" -name "*.dylib" -delete 2>/dev/null || true

echo "==> Creating launcher script"
cat > "${BUILDROOT}/usr/bin/${APP_NAME}" << 'LAUNCHER'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${SCRIPT_DIR}/opt/pdfsigner/lib:${PYTHONPATH:-}"
exec python3 -m pdfsigner "$@"
LAUNCHER
chmod 755 "${BUILDROOT}/usr/bin/${APP_NAME}"

echo "==> Installing icon"
if [ -f "${ROOT_DIR}/packaging/pdfsigner.png" ]; then
    cp "${ROOT_DIR}/packaging/pdfsigner.png" "${BUILDROOT}/usr/share/icons/hicolor/256x256/apps/pdfsigner.png"
    echo "Icon installed successfully"
else
    echo "WARNING: Icon file not found"
fi

echo "==> Installing desktop file"
cat > "${BUILDROOT}/usr/share/applications/${APP_NAME}.desktop" << 'EOF'
[Desktop Entry]
Name=PDF Signer Linux
Comment=PDF signing and visible stamp tool for Linux with CryptoPro CSP
Exec=pdfsigner
Icon=pdfsigner
Terminal=false
Type=Application
Categories=Utility;Security;
Keywords=pdf;sign;crypto;stamp;
EOF

echo "==> Installing documentation"
cp "${ROOT_DIR}/README.md" "${BUILDROOT}/usr/share/doc/${APP_NAME}/" 2>/dev/null || true
cp "${ROOT_DIR}/LICENSE" "${BUILDROOT}/usr/share/doc/${APP_NAME}/COPYING" 2>/dev/null || true

echo "==> Calculating installed size"
INSTALLED_SIZE=$(du -sk "${BUILDROOT}" | cut -f1)

echo "==> Creating DEB control file"
cat > "${BUILDROOT}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Installed-Size: ${INSTALLED_SIZE}
Maintainer: shurshick <noreply@example.com>
Homepage: https://github.com/shurshick/pdf-signer-linux
Depends: python3 (>= 3.9), python3-pyqt5, python3-pyqt5.qtsvg, libgl1-mesa-glx | libgl1, libglib2.0-0, libx11-6
Recommends: libcryptopro-java
Description: Desktop PDF signing and visible stamp tool for Linux with CryptoPro CSP
 Desktop application for signing PDF documents with CryptoPro CSP
 on Linux. Supports embedded CAdES-BES signatures via PKCS#11, visible
 stamps compliant with GOST R 7.0.97-2025, signature verification, and
 CryptoPro diagnostics.
 .
 Requires python3 and system Qt libraries.
EOF

echo "==> Building DEB"
dpkg-deb --build --root-owner-group "${BUILDROOT}" "${DIST_DIR}/${APP_NAME}_${VERSION}_amd64.deb"

echo "==> Done"
echo "Version: ${VERSION}"
echo "DEB package:"
ls -lh "${DIST_DIR}"/*.deb
