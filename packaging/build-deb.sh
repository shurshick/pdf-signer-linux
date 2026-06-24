#!/bin/bash
set -euo pipefail

APP_NAME="pdfsigner"
VERSION="${VERSION:-1.0.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
BUILDROOT="${ROOT_DIR}/.debbuild"

echo "==> Checking project files"
for f in "${ROOT_DIR}/pyproject.toml" "${ROOT_DIR}/README.md"; do
    if [ ! -f "$f" ]; then
        echo "Error: $f not found"
        exit 1
    fi
done

echo "==> Cleaning previous build output"
rm -rf "${BUILDROOT}" "${DIST_DIR}"
mkdir -p "${BUILDROOT}/DEBIAN" \
    "${BUILDROOT}/usr/bin" \
    "${BUILDROOT}/usr/share/applications" \
    "${BUILDROOT}/usr/share/icons/hicolor/256x256/apps" \
    "${BUILDROOT}/usr/share/doc/${APP_NAME}" \
    "${BUILDROOT}/opt/${APP_NAME}" \
    "${DIST_DIR}"

echo "==> Building Python wheel"
cd "${ROOT_DIR}"
pip install build 2>/dev/null || true
python3 -m build --wheel --outdir "${DIST_DIR}"

echo "==> Installing package files"
cp "${DIST_DIR}"/*.whl "${BUILDROOT}/opt/${APP_NAME}/"
cp "${DIST_DIR}"/*.tar.gz "${BUILDROOT}/opt/${APP_NAME}/" 2>/dev/null || true

cat > "${BUILDROOT}/usr/bin/${APP_NAME}" << 'LAUNCHER'
#!/bin/bash
pip install --user /opt/pdfsigner/*.whl 2>/dev/null
exec python3 -m pdfsigner "$@"
LAUNCHER
chmod 755 "${BUILDROOT}/usr/bin/${APP_NAME}"

if [ -f "${ROOT_DIR}/packaging/pdfsigner.png" ]; then
    cp "${ROOT_DIR}/packaging/pdfsigner.png" "${BUILDROOT}/usr/share/icons/hicolor/256x256/apps/"
fi

cat > "${BUILDROOT}/usr/share/applications/${APP_NAME}.desktop" << 'EOF'
[Desktop Entry]
Name=PDF Signer Linux
Comment=PDF signing and visible stamp tool
Exec=pdfsigner
Icon=pdfsigner
Terminal=false
Type=Application
Categories=Utility;Security;
EOF

cp "${ROOT_DIR}/README.md" "${BUILDROOT}/usr/share/doc/${APP_NAME}/" 2>/dev/null || true

cat > "${BUILDROOT}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: shurshick <noreply@example.com>
Homepage: https://github.com/shurshick/pdf-signer-linux
Depends: python3 (>= 3.9), python3-pyqt5, python3-pip
Recommends: libcryptopro-java
Description: Desktop PDF signing and visible stamp tool for Linux with CryptoPro CSP
 Desktop application for signing PDF documents with CryptoPro CSP on Linux.
 Supports embedded CAdES-BES signatures via PKCS#11, visible stamps
 compliant with GOST R 7.0.97-2025, signature verification, and
 CryptoPro diagnostics.
EOF

echo "==> Building DEB"
dpkg-deb --build --root-owner-group "${BUILDROOT}" "${DIST_DIR}/${APP_NAME}_${VERSION}_amd64.deb"

echo "==> Done"
echo "Version: ${VERSION}"
echo "DEB packages:"
ls -lh "${DIST_DIR}"/*.deb
