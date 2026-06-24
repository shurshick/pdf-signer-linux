#!/bin/bash
set -euo pipefail

APP_NAME="pdfsigner"
VERSION="${VERSION:-1.0.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
BUILDROOT="${ROOT_DIR}/.rpmbuild"

echo "==> Checking project files"
for f in "${ROOT_DIR}/pyproject.toml" "${ROOT_DIR}/packaging/pdfsigner.desktop" "${ROOT_DIR}/packaging/pdfsigner.png"; do
    if [ ! -f "$f" ]; then
        echo "Error: $f not found"
        exit 1
    fi
done

echo "==> Cleaning previous build output"
rm -rf "${BUILDROOT}"
mkdir -p "${BUILDROOT}"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS} "${DIST_DIR}"

echo "==> Installing Python dependencies"
pip3 install pyinstaller 2>/dev/null || pip install pyinstaller
pip3 install -e "${ROOT_DIR}" 2>/dev/null || pip install -e "${ROOT_DIR}"

echo "==> Building self-contained binary with PyInstaller"
cd "${ROOT_DIR}"
pyinstaller \
    --onefile \
    --name "${APP_NAME}" \
    --distpath "${BUILDROOT}/SOURCES" \
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

echo "==> Preparing RPM sources (like Go project)"
mkdir -p "${BUILDROOT}/SOURCES/packaging"
cp "${ROOT_DIR}/packaging/pdfsigner.desktop" "${BUILDROOT}/SOURCES/packaging/"
cp "${ROOT_DIR}/packaging/pdfsigner.png" "${BUILDROOT}/SOURCES/packaging/"
cp "${ROOT_DIR}/README.md" "${BUILDROOT}/SOURCES/" 2>/dev/null || true
cp "${ROOT_DIR}/LICENSE" "${BUILDROOT}/SOURCES/" 2>/dev/null || true

echo "==> Generating SPEC"
cat > "${BUILDROOT}/SPECS/pdfsigner.spec" << 'SPEC'
Name:           pdfsigner
Version:        VERSION_PLACEHOLDER
Release:        1
Summary:        Desktop PDF signing and visible stamp tool for Linux with CryptoPro CSP

License:        AGPLv3
URL:            https://github.com/shurshick/pdf-signer-linux
BuildArch:      x86_64

AutoReq:        no
AutoProv:       no

Recommends:     cprocsp-pki-plugin
Recommends:     mesa-libGL
Recommends:     mesa-libEGL

%description
Desktop application for signing PDF documents with CryptoPro CSP on Linux.
Supports embedded CAdES-BES signatures via PKCS#11, visible stamps
compliant with GOST R 7.0.97-2025, signature verification, and
CryptoPro diagnostics. Self-contained binary, no Python required.

%prep
# Nothing to unpack.

%build
# Build is done by the external script.

%install
rm -rf %{buildroot}

install -D -m 0755 %{_sourcedir}/pdfsigner %{buildroot}/usr/bin/pdfsigner
install -D -m 0644 %{_sourcedir}/packaging/pdfsigner.desktop %{buildroot}/usr/share/applications/pdfsigner.desktop
install -D -m 0644 %{_sourcedir}/packaging/pdfsigner.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/pdfsigner.png
install -D -m 0644 %{_sourcedir}/README.md %{buildroot}/usr/share/doc/pdfsigner/README.md 2>/dev/null || true
install -D -m 0644 %{_sourcedir}/LICENSE %{buildroot}/usr/share/doc/pdfsigner/COPYING 2>/dev/null || true

%files
/usr/bin/pdfsigner
/usr/share/applications/pdfsigner.desktop
/usr/share/icons/hicolor/256x256/apps/pdfsigner.png
/usr/share/doc/pdfsigner/

%changelog
* Sun Jun 22 2026 shurshick <noreply@example.com> - VERSION_PLACEHOLDER-1
- Initial release with embedded PDF signing, GOST-compliant stamps,
  signature verification, and CryptoPro diagnostics.
SPEC

sed -i "s/VERSION_PLACEHOLDER/${VERSION}/g" "${BUILDROOT}/SPECS/pdfsigner.spec"

echo "==> Building RPM"
rpmbuild -bb "${BUILDROOT}/SPECS/pdfsigner.spec" \
    --define "_topdir ${BUILDROOT}" \
    --define "_sourcedir ${BUILDROOT}/SOURCES" \
    --define "_specdir ${BUILDROOT}/SPECS" \
    --define "_builddir ${BUILDROOT}/BUILD" \
    --define "_buildrootdir ${BUILDROOT}/BUILDROOT" \
    --define "_rpmdir ${BUILDROOT}/RPMS" \
    --define "_srcrpmdir ${BUILDROOT}/SRPMS"

echo "==> Copying RPM to dist/"
find "${BUILDROOT}/RPMS" -type f -name "*.rpm" -exec cp -f {} "${DIST_DIR}/" \;

echo "==> Done"
echo "Version: ${VERSION}"
echo "RPM package:"
ls -lh "${DIST_DIR}"/*.rpm
