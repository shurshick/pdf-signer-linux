#!/bin/bash
set -euo pipefail

APP_NAME="pdfsigner"
VERSION="${VERSION:-1.0.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
BUILDROOT="${ROOT_DIR}/.debbuild"

echo "==> Checking project files"
for f in "${ROOT_DIR}/pyproject.toml" "${ROOT_DIR}/packaging/pdfsigner.desktop" "${ROOT_DIR}/packaging/pdfsigner.png"; do
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
    "${DIST_DIR}"

echo "==> Installing Python dependencies"
pip3 install pyinstaller 2>/dev/null || pip install pyinstaller
pip3 install -e "${ROOT_DIR}" 2>/dev/null || pip install -e "${ROOT_DIR}"

echo "==> Building self-contained binary with PyInstaller"
cd "${ROOT_DIR}"
pyinstaller \
    --onefile \
    --name "${APP_NAME}" \
    --distpath "${DIST_DIR}" \
    --workpath "${ROOT_DIR}/build" \
    --specpath "${ROOT_DIR}" \
    --hidden-import pdfsigner \
    --hidden-import pdfsigner.gui \
    --hidden-import pdfsigner.signer \
    --hidden-import pdfsigner.stamp \
    --hidden-import pdfsigner.pdfstamp \
    --hidden-import pdfsigner.certstore \
    --hidden-import pdfsigner.settings \
    --hidden-import pdfsigner.diagnostics \
    --hidden-import pdfsigner.applog \
    --collect-all pdfsigner \
    --noconfirm \
    pdfsigner/main.py

echo "==> Installing binary (like Go project)"
install -D -m 0755 "${DIST_DIR}/${APP_NAME}" "${BUILDROOT}/usr/bin/${APP_NAME}"

echo "==> Installing desktop file (like Go project)"
install -D -m 0644 "${ROOT_DIR}/packaging/pdfsigner.desktop" "${BUILDROOT}/usr/share/applications/${APP_NAME}.desktop"

echo "==> Installing icon (like Go project)"
install -D -m 0644 "${ROOT_DIR}/packaging/pdfsigner.png" "${BUILDROOT}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"

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
Depends: libc6, libgl1-mesa-glx | libGL, libglib2.0-0, libx11-6
Recommends: libcryptopro-java
Description: Desktop PDF signing and visible stamp tool for Linux with CryptoPro CSP
 Desktop application for signing PDF documents with CryptoPro CSP
 on Linux. Supports embedded CAdES-BES signatures via PKCS#11, visible
 stamps compliant with GOST R 7.0.97-2025, signature verification, and
 CryptoPro diagnostics. Self-contained binary, no Python required.
EOF

echo "==> Building DEB"
dpkg-deb --build --root-owner-group "${BUILDROOT}" "${DIST_DIR}/${APP_NAME}_${VERSION}_amd64.deb"

echo "==> Done"
echo "Version: ${VERSION}"
echo "DEB package:"
ls -lh "${DIST_DIR}"/*.deb
