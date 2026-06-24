Name:           pdfsigner
Version:        1.0.0
Release:        1
Summary:        Desktop PDF signing and visible stamp tool for Linux with CryptoPro CSP

License:        AGPLv3
URL:            https://github.com/shurshick/pdf-signer-linux
BuildArch:      x86_64

Requires:       python3 >= 3.9
Requires:       python3-pyqt5
Requires:       python3-pip

%description
Desktop application for signing PDF documents with CryptoPro CSP on Linux.
Supports embedded CAdES-BES signatures via PKCS#11, visible stamps
compliant with GOST R 7.0.97-2025, signature verification, and
CryptoPro diagnostics.

%prep
# Nothing to unpack - binary is pre-built.

%build
# Build is done by the external script.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/pdfsigner
cp -f %{_sourcedir}/*.whl %{buildroot}/opt/pdfsigner/
cp -f %{_sourcedir}/*.tar.gz %{buildroot}/opt/pdfsigner/ 2>/dev/null || true

mkdir -p %{buildroot}/usr/bin
cat > %{buildroot}/usr/bin/pdfsigner << 'EOF'
#!/bin/bash
exec pip install --user /opt/pdfsigner/*.whl 2>/dev/null
exec python3 -m pdfsigner "$@"
EOF
chmod 755 %{buildroot}/usr/bin/pdfsigner

mkdir -p %{buildroot}/usr/share/applications
cat > %{buildroot}/usr/share/applications/pdfsigner.desktop << 'EOF'
[Desktop Entry]
Name=PDF Signer Linux
Comment=PDF signing and visible stamp tool
Exec=pdfsigner
Icon=pdfsigner
Terminal=false
Type=Application
Categories=Utility;Security;
EOF

mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
cp -f %{_sourcedir}/pdfsigner.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/ 2>/dev/null || true

mkdir -p %{buildroot}/usr/share/doc/pdfsigner
cp -f %{_sourcedir}/README.md %{buildroot}/usr/share/doc/pdfsigner/ 2>/dev/null || true

%files
/opt/pdfsigner/
/usr/bin/pdfsigner
/usr/share/applications/pdfsigner.desktop
/usr/share/doc/pdfsigner/

%changelog
* Sun Jun 23 2026 shurshick <noreply@example.com> - 1.0.0-1
- Initial release with embedded PDF signing, GOST-compliant stamps,
  signature verification, and CryptoPro diagnostics.
