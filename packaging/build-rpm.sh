#!/bin/bash
set -euo pipefail

APP_NAME="pdfsigner"
VERSION="${VERSION:-1.0.0}"
RELEASE="${RELEASE:-1}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
BUILDROOT="${ROOT_DIR}/.rpmbuild"
VENV_DIR="${BUILDROOT}/install/opt/${APP_NAME}"

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

echo "==> Creating virtualenv with all dependencies"
python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install "${ROOT_DIR}"

echo "==> Preparing RPM sources"
cp "${ROOT_DIR}/packaging/pdfsigner.png" "${BUILDROOT}/SOURCES/" 2>/dev/null || true
cp "${ROOT_DIR}/packaging/pdfsigner.desktop" "${BUILDROOT}/SOURCES/" 2>/dev/null || true
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

Requires:       python3 >= 3.9

%description
Desktop application for signing PDF documents with CryptoPro CSP on Linux.
Supports embedded CAdES-BES signatures via PKCS#11, visible stamps
compliant with GOST R 7.0.97-2025, signature verification, and
CryptoPro diagnostics. Includes all Python dependencies in an
isolated virtualenv.

%prep
# Nothing to unpack - virtualenv is pre-built.

%build
# Build is done by the external script.

%install
rm -rf %{buildroot}

install -D -m 0755 %{_sourcedir}/../BUILDROOT/install/opt/pdfsigner %{buildroot}/opt/pdfsigner
cp -a %{_sourcedir}/../BUILDROOT/install/opt/pdfsigner/* %{buildroot}/opt/pdfsigner/

mkdir -p %{buildroot}/usr/bin
cat > %{buildroot}/usr/bin/pdfsigner << 'LAUNCHER'
#!/bin/bash
exec /opt/pdfsigner/bin/python3 -m pdfsigner "$@"
LAUNCHER
chmod 755 %{buildroot}/usr/bin/pdfsigner

install -D -m 0644 %{_sourcedir}/pdfsigner.desktop %{buildroot}/usr/share/applications/pdfsigner.desktop
install -D -m 0644 %{_sourcedir}/pdfsigner.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/pdfsigner.png 2>/dev/null || true

mkdir -p %{buildroot}/usr/share/doc/pdfsigner
cp -f %{_sourcedir}/README.md %{buildroot}/usr/share/doc/pdfsigner/ 2>/dev/null || true
cp -f %{_sourcedir}/LICENSE %{buildroot}/usr/share/doc/pdfsigner/COPYING 2>/dev/null || true

%files
/opt/pdfsigner/
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
