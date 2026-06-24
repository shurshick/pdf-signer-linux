#!/bin/bash
set -euo pipefail

APP_NAME="pdfsigner"
VERSION="${VERSION:-1.0.0}"
RELEASE="${RELEASE:-1}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
BUILDROOT="${ROOT_DIR}/.rpmbuild"

echo "==> Checking project files"
for f in "${ROOT_DIR}/pyproject.toml" "${ROOT_DIR}/packaging/rpm/pdfsigner.spec"; do
    if [ ! -f "$f" ]; then
        echo "Error: $f not found"
        exit 1
    fi
done

echo "==> Cleaning previous build output"
rm -rf "${BUILDROOT}"
mkdir -p "${BUILDROOT}"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS} "${DIST_DIR}"

echo "==> Installing Python dependencies"
pip install pyinstaller 2>/dev/null || true
pip install -e "${ROOT_DIR}" 2>/dev/null || pip install "${ROOT_DIR}" 2>/dev/null || true

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

echo "==> Preparing RPM sources"
cp "${ROOT_DIR}/packaging/pdfsigner.png" "${BUILDROOT}/SOURCES/" 2>/dev/null || true
cp "${ROOT_DIR}/README.md" "${BUILDROOT}/SOURCES/" 2>/dev/null || true
cp "${ROOT_DIR}/LICENSE" "${BUILDROOT}/SOURCES/" 2>/dev/null || true
cp "${ROOT_DIR}/packaging/pdfsigner.desktop" "${BUILDROOT}/SOURCES/" 2>/dev/null || true

echo "==> Generating SPEC"
cp "${ROOT_DIR}/packaging/rpm/pdfsigner.spec" "${BUILDROOT}/SPECS/pdfsigner.spec"

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
