#!/bin/bash
set -e

VERSION="${1:-1.0.0}"
ARCH="amd64"
PKG_NAME="pdfsigner"
BUILD_DIR="packaging/deb/${PKG_NAME}_${VERSION}_${ARCH}"

echo "Building DEB package v${VERSION}..."

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/lib/python3/dist-packages/pdfsigner"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/pixmaps"

cat > "$BUILD_DIR/DEBIAN/control" << EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: shurshick <noreply@example.com>
Homepage: https://github.com/shurshick/pdf-signer-linux
Depends: python3 (>= 3.9), python3-pyqt5, python3-pil, python3-pymupdf
Recommends: libcryptopro-java
Description: Desktop PDF signing and visible stamp tool for Linux with CryptoPro CSP
 Desktop application for signing PDF documents with CryptoPro CSP
 on Linux. Supports embedded CAdES-BES signatures via PKCS#11, visible
 stamps compliant with GOST R 7.0.97-2025, signature verification, and
 CryptoPro diagnostics.
 Features include smart stamp placement, logo support, settings export/import,
 bilingual interface, and batch signing.
EOF

cat > "$BUILD_DIR/usr/bin/pdfsigner" << 'EOF'
#!/bin/bash
exec python3 -m pdfsigner "$@"
EOF
chmod +x "$BUILD_DIR/usr/bin/pdfsigner"

cp -r pdfsigner/* "$BUILD_DIR/usr/lib/python3/dist-packages/pdfsigner/"

cat > "$BUILD_DIR/usr/share/applications/pdfsigner.desktop" << EOF
[Desktop Entry]
Name=PDF Signer Linux
Comment=Desktop PDF signing and visible stamp tool
Exec=pdfsigner
Icon=pdfsigner
Terminal=false
Type=Application
Categories=Utility;Security;
EOF

cp app-icon.png "$BUILD_DIR/usr/share/pixmaps/pdfsigner.png" 2>/dev/null || true

dpkg-deb --build "$BUILD_DIR"

echo "DEB package built: ${BUILD_DIR}.deb"
